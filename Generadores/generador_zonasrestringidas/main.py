import json
import requests
import random
import os
from faker import Faker

# --- CONFIGURACIÓN ---
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ARCHIVO_SALIDA = "memoria_zonas.json"
CANTIDAD = 5

fake = Faker('es_ES')

# Coordenadas base para que las zonas caigan en las ciudades correctas
# (Latitud, Longitud)
CIUDADES_COORDS = {
    "Madrid": (40.4168, -3.7038),
    "Barcelona": (41.3851, 2.1734),
    "Valencia": (39.4699, -0.3763)
}

def generar():
    lista_zonas = []
    print(f"--- 1. Generando {CANTIDAD} Zonas Restringidas ---")
    print(f"--- Conectando a: {API_URL}/zonas_restringidas ---")

    for i in range(CANTIDAD):
        
        # 1. Elegimos ciudad y generamos coordenadas cercanas (variación aleatoria)
        nombre_ciudad = random.choice(list(CIUDADES_COORDS.keys()))
        lat_base, lon_base = CIUDADES_COORDS[nombre_ciudad]
        
        # Generamos una desviación pequeña (aprox 1-5km alrededor del centro)
        lat_final = lat_base + random.uniform(-0.04, 0.04)
        lon_final = lon_base + random.uniform(-0.04, 0.04)

        # 2. Lógica de radios (Advertencia > Peligro)
        r_peligro = random.randint(50, 200) # Metros
        r_advertencia = r_peligro + random.randint(20, 100)

        # 3. Objeto Zona (Coincide con tu SQL)
        zona = {
            "nombre": f"Zona {fake.word().capitalize()} - {nombre_ciudad}",
            "latitud": lat_final,
            "longitud": lon_final,
            "radio_peligro": r_peligro,
            "radio_advertencia": r_advertencia
        }

        # 4. Enviar a la API
        try:
            # Asegúrate que el endpoint en tu FastAPI sea /zonas_restringidas
            resp = requests.post(f"{API_URL}/zonas_restringidas", json=zona)

            if resp.status_code == 201 or resp.status_code == 200:
                print(f"[{i+1}/{CANTIDAD}] [OK] Zona creada en {nombre_ciudad}")
                lista_zonas.append(zona)
            else:
                print(f"[{i+1}/{CANTIDAD}] [ERROR {resp.status_code}] API: {resp.text}")

        except requests.exceptions.ConnectionError:
            print(f"[{i+1}/{CANTIDAD}] [ERROR CRÍTICO] No conecta a {API_URL}")
        except Exception as e:
            print(f"[{i+1}/{CANTIDAD}] [ERROR] Excepción: {e}")

    # 5. Guardar respaldo
    if lista_zonas:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(lista_zonas, f, indent=4, ensure_ascii=False)
        print(f"\n--- ÉXITO: {len(lista_zonas)} zonas guardadas en {ARCHIVO_SALIDA} ---")

if __name__ == "__main__":
    generar()