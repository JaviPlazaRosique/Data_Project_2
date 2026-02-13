import requests
import os
import random
import uuid

url_api = os.getenv("URL_API")

def obtener_id_direccion_menores():
    try:
        response = requests.get(f"{url_api}/menores/id_direccion")

        response.raise_for_status()

        return response.json().get("menores", [])
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener los IDs y direccionesº de los menores: {e}")
        return []

def generar_coordenadas_ciudad(direccion):
    ciudad = direccion.split(",")[0].strip()
    
    coordenadas = {
        "Madrid": (40.4168, -3.7038),
        "Barcelona": (41.3851, 2.1734),
        "Valencia": (39.4699, -0.3763)
    }
    
    centro_ciudad = coordenadas.get(ciudad, (40.4168, -3.7038))
    
    latitud = centro_ciudad[0] + random.uniform(-0.045, 0.045)
    longitud = centro_ciudad[1] + random.uniform(-0.045, 0.045)
    
    return latitud, longitud

if __name__ == "__main__":
    menores = obtener_id_direccion_menores()
    nombres_zonas = ["Zona Peligrosa", "Vivienda del bully del menor", "Zona MUY Peligrosa"]

    if menores:
        print(f"Generando zonas restringidas para {len(menores)} menores.")
        for menor in menores:
            for _ in range(random.randint(2, 5)):
                lat, lon = generar_coordenadas_ciudad(menor['direccion'])
                radio_peligro = random.randint(50, 200)
                
                zona = {
                    "id": str(uuid.uuid4()),
                    "id_menor": menor['id'],
                    "nombre": random.choice(nombres_zonas),
                    "latitud": lat,
                    "longitud": lon,
                    "radio_peligro": radio_peligro,
                    "radio_advertencia": radio_peligro + random.randint(20, 100)
                }
                
                try:
                    response = requests.post(f"{url_api}/zonas_restringidas", json=zona)

                    if response.status_code == 201:
                        print(f"Zona restringida creada para menor {menor['id']}")
                    else:
                        print(f"Error creando zona: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"Error enviando zona restringida: {e}")
