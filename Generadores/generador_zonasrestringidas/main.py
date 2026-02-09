import json
import requests
import random
from faker import Faker

# # --- CONFIGURACION ---
# API_URL = "http://localhost:8000/api/v1/zonas-restringidas"
ARCHIVO_SALIDA = "datos_zonas.json"
CANTIDAD = 5

fake = Faker('es_ES')

# Coordenadas centrales aproximadas para generar zonas cercanas
COORDENADAS_BASE = {
    "Madrid":    {"lat": 40.4168, "lon": -3.7038},
    "Barcelona": {"lat": 41.3851, "lon": 2.1734},
    "Valencia":  {"lat": 39.4699, "lon": -0.3763}
}

def generar():
    lista_zonas = []
    print(f"Generando {CANTIDAD} zonas restringidas en Madrid, BCN y Valencia...")

    # 1. GENERAR DATOS EN MEMORIA
    for _ in range(CANTIDAD):
        
        # Elegimos una ciudad al azar
        ciudad_elegida = random.choice(list(COORDENADAS_BASE.keys()))
        base = COORDENADAS_BASE[ciudad_elegida]

        # Generamos una desviación pequeña (aprox +/- 5km) para que no caigan todas en el mismo punto
        desviacion_lat = random.uniform(-0.05, 0.05)
        desviacion_lon = random.uniform(-0.05, 0.05)

        # Radios
        r_peligro = random.randint(20, 100)
        r_advertencia = r_peligro + random.randint(20, 50)

        zona = {
            "nombre": f"Zona {fake.word().capitalize()} - {ciudad_elegida}",
            "latitud": base["lat"] + desviacion_lat,
            "longitud": base["lon"] + desviacion_lon,
            "radio_peligro": r_peligro,
            "radio_advertencia": r_advertencia,
            "descripcion": fake.sentence() # Campo opcional útil
        }
        
        lista_zonas.append(zona)

    # 2. GUARDAR EN DISCO (COPIA DE SEGURIDAD)
    try:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(lista_zonas, f, indent=4, ensure_ascii=False)
        print(f"GUARDADO LOCAL: {len(lista_zonas)} zonas en {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"ERROR crítico guardando archivo: {e}")
        return

    # # 3. ENVIAR A LA API
    # print(f"Iniciando envío a la API ({API_URL})...")

    # for item in lista_zonas:
    #     try:
    #         r = requests.post(API_URL, json=item, timeout=5)
            
    #         if r.status_code == 200 or r.status_code == 201:
    #             print(f"[API OK] Zona creada: {item['nombre']}")
    #         else:
    #             print(f"[API ERROR] Fallo al crear {item['nombre']}: {r.status_code} - {r.text}")

    #     except requests.exceptions.ConnectionError:
    #         print(f"[API FAIL] No se pudo conectar a {API_URL}. ¿Está encendido el servidor?")
    #         break
    #     except Exception as e:
    #         print(f"[ERROR] Excepción: {e}")

    # print("Proceso finalizado.")

if __name__ == "__main__":
    generar()