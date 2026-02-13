import requests
import os

url_api = os.getenv("URL_API")

def obtener_id_direccion_menores():
    try:
        response = requests.get(f"{url_api}/menores/id_direccion")

        response.raise_for_status()

        return response.json().get("menores", [])
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener los IDs y direccionesº de los menores: {e}")
        return []
