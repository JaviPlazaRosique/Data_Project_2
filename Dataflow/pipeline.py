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
import psycopg2
import time

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


class LeerZonasPostgres(beam.DoFn):
    """Se conecta a PostgreSQL y extrae las zonas restringidas, actualiza las zonas cada 5 min."""
    def __init__(self, host, db, user, password):
        self.host = host
        self.db = db
        self.user = user
        self.password = password
        self.lista_zonas = [] 
        self.ultima_actualizacion = 0  
        self.tiempo_refresco = 300

    def setup(self):
        self.conn = psycopg2.connect(
            host=self.host, database=self.db, user=self.user, password=self.password
        )

    def process (self, element):
        tiempo_actual = time.time()
        if (tiempo_actual - self.ultima_actualizacion) > self.tiempo_refresco or not self.lista_zonas:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id_menor, nombre, latitud, longitud, radio_peligro, radio_advertencia FROM zonas_restringidas;")
                filas = cursor.fetchall()
                
                nuevas_zonas = []
                for fila in filas:
                    zona_dict = {
                        'id_menor': fila[0],
                        'nombre': fila[1],
                        'latitud': float(fila[2]),
                        'longitud': float(fila[3]),
                        'radio_peligro': float(fila[4]),
                        'radio_advertencia': float(fila[5])
                    }
                    nuevas_zonas.append(zona_dict)
                
                self.lista_zonas = nuevas_zonas # Actualiza
                self.ultima_actualizacion = time.time() # Reinicia el reloj
                cursor.close()
                logging.info("¡Zonas actualizadas desde la base de datos!")
                
            except Exception as e:
                logging.error(f" Error actualizando zonas (se usarán las antiguas): {e}")
        
        element['lista_zonas'] = self.lista_zonas
        yield element

    def teardown(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()


class ZonasRestringidas(beam.DoFn):
    """Clase para comparar la ubicación del menor con las zonas restringidas establecidas por el padre"""
   
    def process(self, element):
        # element =  #Diccionario con datos de la ubicacion del niño (viene del Pub/Sub) y Lista con todas las zonas (viene de la BD)
        try:
            id_menor=element.get('id_menor')
            lat_menor=float(element.get('latitud'))
            long_menor=float(element.get('longitud'))
            lista_zonas = element.get('lista_zonas', [])

        except Exception as e:
            logging.error(f" ERROR procesando coordenadas: {e} | Dato recibido: {element}")
            return
        
        estado = "OK" 

        for zona in lista_zonas:
            if id_menor == zona.get('id_menor'): 
                lat_zona=float(zona.get('latitud'))
                long_zona=float(zona.get('longitud'))
                radio_peligro = float(zona.get('radio_peligro'))
                radio_advertencia = float(zona.get('radio_advertencia'))

                distancia_metros = geodesic((lat_menor, long_menor), (lat_zona, long_zona)).meters
                if distancia_metros < radio_peligro:
                    estado = "PELIGRO"
                    break
                
                elif distancia_metros < radio_advertencia:
                    if estado != "PELIGRO":
                        estado = "ADVERTENCIA"
            else:
                continue
        element['estado'] = estado

        if 'fecha' not in element:
            element['fecha'] = datetime.now().isoformat()

        if 'lista_zonas' in element:
            del element['lista_zonas']
        
        logging.info(f"Procesado: Niño {id_menor} -> Estado: {estado})")        

        yield element    

class EnviarNotificaciones(beam.DoFn):
    """Clase para enviar notificaciones al padre o al menor dependiendo del estado detectado."""
    def process(self, element):
        estado = element.get('estado')

        if estado == "OK":
            logging.info(f"OK: El niño {element.get('id_menor')} está en una zona segura. No se requiere notificación.")  
         
        else:
            id_menor = element.get('id_menor')
            mensaje_alerta = None

            if estado == "PELIGRO":
                logging.warning(f"🚨 ALERTA ROJA: El niño {id_menor} ha entrado en una zona de PELIGRO). Notificando al padre.")
                mensaje_alerta = {
                "destinatario": "PADRE",
                "asunto": f"¡ALERTA DE {estado}!",
                "cuerpo": f"Atención: {id_menor} ha entrado en una zona de peligro. Por favor, verifique su ubicación.",
                "fecha y hora": element.get('fecha', datetime.now().isoformat())
            }
            
            elif estado == "ADVERTENCIA":
                logging.info(f"⚠️ ADVERTENCIA: El niño {id_menor} esta cerca de la zona restringida.")
                mensaje_alerta = {
                "destinatario": "MENOR",
                "asunto": f"¡ALERTA DE {estado}!",
                "cuerpo": f"Atención: {id_menor} ha entrado en zona de advertencia.",
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

        # ubicacion
        doc_ref_ubic = self.db.collection('ubicaciones').document(id_menor)
        datos_ubicacion = {
            "latitud": element['latitud'],
            "longitud": element['longitud'],
            "estado": estado,
            "fecha": firestore.SERVER_TIMESTAMP 
        }
        doc_ref_ubic.set(datos_ubicacion, merge=True) #merge=true para que no borre datos anteriores como info del niño, solo actualiza la ubicacion y el estado.
        logging.info(f"Ubicación actualizada: {id_menor}")

        # notificaciones

        if estado != "OK": 
            

            if estado == "PELIGRO":
                    destinatario = "PADRE"
                    mensaje = f"¡Alerta! {id_menor} ha entrado en una zona prohibida."
            else: # ADVERTENCIA
                    destinatario = "MENOR"
                    mensaje = f"Ten cuidado, está acercándote a una zona restringida."
            datos_alerta = {
                "id_menor": id_menor,
                "asunto": f"¡ALERTA DE {estado}!", # PELIGRO o ADVERTENCIA
                "cuerpo": mensaje,
                "destinatario": destinatario,
                "fecha": firestore.SERVER_TIMESTAMP,
                "leido": False
            }
            doc_ref_alerta = self.db.collection('notificaciones').add(datos_alerta)

            logging.info(f"Documento de notificación escrito en Firestore: {doc_ref_alerta[1].id}")

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
                '--historico_notificaciones_bigquery_table',
                required=False,
                default='historico_notificaciones',
                help='Tabla BigQuery para historico de notificaciones.')
    parser.add_argument(
                '--db_host', 
                required=True, 
                help='IP privada de Cloud SQL.')
    parser.add_argument(
                '--db_user', 
                required=False, 
                default='admin', 
                help='Usuario de la BD.')
    parser.add_argument(
                '--db_pass', 
                required=True, 
                help='Contraseña de la BD.')

    
    args, pipeline_opts = parser.parse_known_args()

    # Pipeline Options
    
    pipeline_opts.append('--temp_location')
    pipeline_opts.append('gs://dataflow-temp-' + args.project_id + '/temp') #aca guarda BQ los datos de las zonas
    options = PipelineOptions(pipeline_opts, 
                              save_main_session=True, 
                              streaming=True, 
                              project=args.project_id,
                              service_account_email="dataflow-worker-sa@" + args.project_id + ".iam.gserviceaccount.com")
    # Pipeline Object
    with beam.Pipeline(argv=pipeline_opts,options=options) as p:
        
        mensajes_procesados = (
            p
                | "LeerDeUbicacionPubSub" >> beam.io.ReadFromPubSub(subscription=f'projects/{args.project_id}/subscriptions/{args.ubicacion_pubsub_subscription_name}')
                | "TransformarMensajePubSub">> beam.Map(TransformacionPubSub)
                | "FiltrarVacios" >> beam.Filter(lambda x: x is not None) #ver si es necesario o lo sacamos pq los mensajes vana a venir siempre con la info que queremos
                | "VentanaDeTiempo" >> beam.WindowInto(beam.window.FixedWindows(10), allowed_lateness=beam.utils.timestamp.Duration(seconds=5)) # Agrupamos los datos en bloques de 10 segundos
                | "LeerZonasPostgres" >> beam.ParDo(LeerZonasPostgres(
                    host=args.db_host, 
                    db="menores_db", 
                    user=args.db_user, 
                    password=args.db_pass
                ))
                | "CompararConZonasRestringidas" >> beam.ParDo(ZonasRestringidas())   
        )

        (mensajes_procesados
                | "EnviarNotificaciones" >> beam.ParDo(EnviarNotificaciones())
                | "ImprimirEnPantalla" >> beam.Map(print)
        )
        
        (mensajes_procesados 
                | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                        project=args.project_id,
                        dataset=args.bigquery_dataset,
                        table=args.historico_notificaciones_bigquery_table,
                        schema='id:STRING, id_menor:STRING, latitud:FLOAT, longitud:FLOAT, fecha:TIMESTAMP, estado:STRING',                        
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


        # #para hacer pruebas en local usamos: 
        # # pegando en otrs consola: gcloud pubsub topics publish topic-ubicacion --message '{"id_menor": "Javi", "latitud": 39.4699, "longitud": -0.3763}'
        # datos_simulados_bq = [{
        #     'id_menor': 'Javi',           # ID del niño que probaremos
        #     'nombre': 'Zona Centro',
        #     'latitud': 39.4699,          # Plaza del Ayto. Valencia
        #     'longitud': -0.3763,
        #     'radio_peligro': 100,        # 100 metros
        #     'radio_advertencia': 500     # 500 metros
        # }]


        # zonas_restringidas = (
        #     p 
        #     | "CrearZonasSimuladas" >> beam.Create(datos_simulados_bq)
        # )