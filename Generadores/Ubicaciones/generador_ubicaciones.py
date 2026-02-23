from random_movement import PersonMovementGenerator
import requests
import json
import os
import threading
import time

url_api = os.getenv("URL_API")
api_key = os.getenv("API_KEY")

class MandarDatoAPI(PersonMovementGenerator):
    def write_element(self, position, filename, mode='a'):
        try:
            ubicacion = {
                "id_menor": str(position['user_id']),
                "timestamp": position['timestamp'],
                "latitud": float(position['latitude']),
                "longitud": float(position['longitude'])
            }
            response = requests.post(f"{url_api}/ubicaciones", json=ubicacion, headers={"X-API-Key": api_key})
            if response.status_code >= 400:
                print(f"Error enviando ubicacion: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error enviando ubicacion: {e}")

def obtener_id_direccion_menores():
    try:
        response = requests.get(f"{url_api}/menores/id_direccion", headers={"X-API-Key": api_key})

        response.raise_for_status()

        return response.json().get("menores", [])
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener los IDs y direccionesº de los menores: {e}")
        return []

def generar_movimiento(menor):
    try:
        print(f"Iniciando generador para menor {menor['id']} en {menor['direccion']}")

        generador = MandarDatoAPI(place_name=menor['direccion'])
        
        generador.generate_continuous_movement(output_file="/dev/null", user_id=menor['id'])
    except Exception as e:
        print(f"Error generando movimiento para menor {menor['id']}: {e}")

if __name__ == "__main__":
    menores = obtener_id_direccion_menores()
    threads = []
    
    for menor in menores:
        t = threading.Thread(target=generar_movimiento, args=(menor,))
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()