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
import uuid
import json

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
    
    args, pipeline_opts = parser.parse_known_args()

    # Pipeline Options
    options = PipelineOptions(pipeline_opts, save_main_session=True, streaming=True, project=args.project_id)

    # Pipeline Object
    with beam.Pipeline(argv=pipeline_opts,options=options) as p:

        (
            p
                | "LeerDeUbicacionPubSub" >> beam.io.ReadFromPubSub(subscription=f'projects/{args.project_id}/subscriptions/{args.ubicacion_pubsub_subscription_name}')
                | "TransformarMensajePubSub">> beam.Map(TransformacionPubSub)
                # | "CompararConZonasRestringidas" >>
                | beam.Map(print)
        )

if __name__ == '__main__':

    # Habilitar Logs
    logging.basicConfig(level=logging.INFO)

    # Deshabilitar logs de apache_beam.utils.subprocess_server
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)

    logging.info("The process started")

    # Run Process
    run()