""" 
Script: Dataflow Streaming Pipeline

Descripción: Monitoreo de la ubicacion de un menor en tiempo real comparando con las zonas prohibidas que su padre ha establecido. 
En caso de que el menor entre a una zona de advertencia, se le enviará notificacion al menor y si entra en zona prohibida, 
se le enviará una notificación al padre.

"""
# A. Librerias Apache Beam 
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.window import Sessions, SlidingWindows
from apache_beam.io.filesystems import FileSystems
from apache_beam.utils.timestamp import Timestamp


# B. Librerias Python 
import argparse
import logging
import json
from geopy.distance import geodesic
from datetime import datetime
from google.cloud import firestore

def TransformacionPubSub(message):
    """Función para transformar los mensajes de Pub/Sub a un formato adecuado para el procesamiento, si falla devuelve None para no romper el proceso."""
    try:    
            # Convertir el mensaje de bytes a string
        message_str = message.decode('utf-8')
            # Parsear el string como JSON
        message_json = json.loads(message_str)
        return message_json
    
    except Exception as e:
        logging.error(f"Error al parsear mensaje: {e}")
        return None


class ZonasRestringidas(beam.DoFn):
    """Clase para comparar la ubicación del menor con las zonas restringidas establecidas por el padre"""
   
    def process(self, element, lista_zonas):
        # element =  #Diccionario con datos de la ubicacion del niño (viene del Pub/Sub)
        # lista_zonas = #Lista con todas las zonas (viene de BigQuery)
        try:
            id_menor=element.get('id_menor')
            lat_menor=float(element.get('latitud'))
            long_menor=float(element.get('longitud'))

        except:
            return
        
        estado = "OK" 
        zona_detectada = None

        for zona in lista_zonas:
            if id_menor == zona.get('id_menor'): 
                lat_zona=float(zona.get('latitud'))
                long_zona=float(zona.get('longitud'))
                radio_peligro = float(zona.get('radio_peligro'))
                radio_advertencia = float(zona.get('radio_advertencia'))

                distancia_metros = geodesic((lat_menor, long_menor), (lat_zona, long_zona)).meters
                if distancia_metros < radio_peligro:
                    estado = "PELIGRO"
                    zona_detectada = zona['nombre']
                    break # Es lo peor que puede pasar, dejamos de mirar
                
                elif distancia_metros < radio_advertencia:
                    if estado != "PELIGRO":
                        estado = "ADVERTENCIA"
                        zona_detectada = zona['nombre']

            else:
                continue
        element['estado'] = estado
        element['zona_involucrada'] = zona_detectada

        if 'fecha' not in element:
            element['fecha'] = datetime.now().isoformat()

        logging.info(f"Procesado: Niño {id_menor} -> Estado: {estado} (Zona: {zona_detectada})")        

        yield element    

class EnviarNotificaciones(beam.DoFn):
    """Clase para enviar notificaciones al padre o al menor dependiendo del estado detectado."""
    def process(self, element):
        estado = element.get('estado')

        if estado == "OK":
            logging.info(f"OK: El niño {element.get('id_menor')} está en una zona segura. No se requiere notificación.")  
         
        else:
            id_menor = element.get('id_menor')
            zona = element.get('zona_involucrada')
            mensaje_alerta = None

            if estado == "PELIGRO":
                logging.warning(f"🚨 ALERTA ROJA: El niño {id_menor} ha entrado en una zona de PELIGRO ({zona}). Notificando al padre.")
                mensaje_alerta = {
                "destinatario": "PADRE", # Aquí iría el email/teléfono real
                "asunto": f"¡ALERTA DE {estado}!",
                "cuerpo": f"Atención: {id_menor} ha entrado en la zona {zona}. Por favor, verifique su ubicación.",
                "fecha y hora": element.get('fecha', datetime.now().isoformat())
            }
            
            elif estado == "ADVERTENCIA":
                logging.info(f"⚠️ ADVERTENCIA: El niño {id_menor} cerca de zona ({zona}). Notificando al menor.")
                mensaje_alerta = {
                "destinatario": "MENOR",
                "asunto": f"¡ALERTA DE {estado}!",
                "cuerpo": f"Atención: {id_menor} ha entrado en la zona restringida de {zona}.",
                "fecha y hora": element.get('fecha', datetime.now().isoformat())
            }
           
            else:
                logging.info(f"OK: El niño {id_menor} está en una zona segura.")


            if mensaje_alerta:
                yield json.dumps(mensaje_alerta)


class GuardarEnFirestore(beam.DoFn):
    """Clase para guardar el historial de ubicaciones en Firestore."""
    def __init__(self, project_id):
        self.project_id = project_id

    def setup(self):
        self.db = firestore.Client(project=self.project_id)

    def process(self, element):
        id_menor = element['id_menor']
        estado = element['estado']
        zona = element.get('zona_involucrada', 'Desconocida')

        # --- COLECCIÓN 1: Ubicaciones en Tiempo Real ---
        # Aquí guardamos solo la posición actual. 
        doc_ubicacion = self.db.collection('ubicaciones_actualizadas').document(id_menor) # Si el niño se mueve, se borra la posición vieja y se pone la nueva.
        doc_ubicacion.set({
            'latitud': element['latitud'],
            'longitud': element['longitud'],
            'fecha': firestore.SERVER_TIMESTAMP,
            'estado': estado
        })

        # --- COLECCIÓN 2: Alertas para el NIÑO (Advertencia) ---
        # Solo entramos aquí si el estado es ADVERTENCIA.
        if estado == "ADVERTENCIA":
            self.db.collection('alertas_niño').add({
                'id_menor': id_menor,
                'mensaje': f"¡Cuidado! Te estás acercando a la zona: {zona}",
                'fecha': firestore.SERVER_TIMESTAMP
            })

        # --- COLECCIÓN 3: Alertas para el PADRE (Peligro) ---
        # Solo entramos aquí si el estado es PELIGRO.
        elif estado == "PELIGRO":
            self.db.collection('alertas_padre').add({
                'id_menor': id_menor,
                'mensaje': f"¡ALERTA! El menor ha entrado en la zona prohibida: {zona}",
                'fecha': firestore.SERVER_TIMESTAMP
            })

        yield element




""" Codigo: Proceso de Dataflow  """

def run():

    """ Argumentos de entrada para la ejecución del pipeline. """
    parser = argparse.ArgumentParser(description=('Argumentos para Dataflow Streaming Pipeline.'))

    parser.add_argument(
                '--project_id',
                required=False,
                default='dataflow-marina',
                help='nombre del proyecto en GCP.')
    
    parser.add_argument(
                '--ubicacion_pubsub_subscription_name',
                required=False,
                default='topic-ubicacion-sub',
                help='subscripcion de ubicacion de menores en Pub/Sub.')
    parser.add_argument(
                '--bigquery_dataset',
                required=False,
                default='monitoreo_dataset',
                help='BigQuery dataset name.')
    parser.add_argument(
                '--tabla_zonas',
                required=False,
               default='dataflow-marina:monitoreo_dataset.zona-restringida',
                help='Tabla BigQuery con zonas restringidas.')
    parser.add_argument(
                '--historico_ubicacion_bigquery_table',
                required=False,
                default='historico_ubicacion',
                help='Tabla BigQuery para historico de ubicaciones.')

    
    args, pipeline_opts = parser.parse_known_args()

    # Pipeline Options
    options = PipelineOptions(pipeline_opts, 
                              save_main_session=True, 
                              streaming=True, 
                              project=args.project_id,
                              service_account_email="dataflow-worker-sa@" + args.project_id + ".iam.gserviceaccount.com")
    pipeline_opts.append('--temp_location')
    pipeline_opts.append('gs://dataflow-jamagece/temp') #aca guarda BQ los datos de las zonas

    # Pipeline Object
    with beam.Pipeline(argv=pipeline_opts,options=options) as p:
        #
        # zonas_restringidas = (
        #     p 
        #     | "LeerZonasBQ" >> beam.io.ReadFromBigQuery(table=args.tabla_zonas)
        # )

        #para hacer pruebas en local usamos: 
        # pegando en otrs consola: gcloud pubsub topics publish topic-ubicacion --message '{"id_menor": "Javi", "latitud": 39.4699, "longitud": -0.3763}'
        datos_simulados_bq = [{
            'id_menor': 'Javi',           # ID del niño que probaremos
            'nombre': 'Zona Centro',
            'latitud': 39.4699,          # Plaza del Ayto. Valencia
            'longitud': -0.3763,
            'radio_peligro': 100,        # 100 metros
            'radio_advertencia': 500     # 500 metros
        }]


        zonas_restringidas = (
            p 
            | "CrearZonasSimuladas" >> beam.Create(datos_simulados_bq)
        )

        mensajes_procesados = (
            p
                | "LeerDeUbicacionPubSub" >> beam.io.ReadFromPubSub(subscription=f'projects/{args.project_id}/subscriptions/{args.ubicacion_pubsub_subscription_name}')
                | "TransformarMensajePubSub">> beam.Map(TransformacionPubSub)
                | "FiltrarVacios" >> beam.Filter(lambda x: x is not None) #ver si es necesario o lo sacamos pq los mensajes vana a venir siempre con la info que queremos
                | "VentanaDeTiempo" >> beam.WindowInto(beam.window.FixedWindows(10)), allowed_lateness=beam.utils.timestamp.Duration(seconds=5), # Agrupamos los datos en bloques de 10 segundos
                | "CompararConZonasRestringidas" >> beam.ParDo(ZonasRestringidas(), beam.pvalue.AsList(zonas_restringidas))
                
        )
        (mensajes_procesados
                | "EnviarNotificaciones" >> beam.ParDo(EnviarNotificaciones())
                | "ImprimirEnPantalla" >> beam.Map(print)
        )
        
        (mensajes_procesados 
                | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                        project=args.project_id,
                        dataset=args.bigquery_dataset,
                        table=args.historico_ubicacion_bigquery_table,
                        schema='id:STRING, fecha:TIMESTAMP, latitud:FLOAT, longitud:FLOAT, radio:FLOAT, direccion:INTEGER, duracion:INT64, id_menor:STRING, estado:STRING, zona_involucrada:STRING',                        
                        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
                    )
        )
        (mensajes_procesados
            | "GuardarEnFirestore" >> beam.ParDo(GuardarEnFirestore(args.project_id)) 
        )
        

if __name__ == '__main__':

    # Habilitar Logs
    logging.basicConfig(level=logging.INFO)

    # Deshabilitar logs de apache_beam.utils.subprocess_server
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)

    logging.info("The process started")

    # Run Process
    run()