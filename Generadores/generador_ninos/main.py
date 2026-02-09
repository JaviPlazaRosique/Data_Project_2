import json
import requests
import random
import os
from faker import Faker

# --- CONFIGURACIÓN ---
# Leemos la variable de entorno API_URL. Si no existe, usa localhost por defecto.
# Esto es vital para Docker.
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

fake = Faker('es_ES')
CANTIDAD = 5
ARCHIVO_SALIDA = "memoria_ninos.json"

# Lista restringida de ciudades
CIUDADES_PERMITIDAS = ["Madrid", "Barcelona", "Valencia"]

def generar():
    lista_memoria = []
    print(f"--- 1. Generando {CANTIDAD} Menores ---")
    print(f"--- Conectando a: {API_URL}/menores ---")

    for i in range(CANTIDAD):
        # Generamos DNI único
        dni = fake.unique.bothify(text='########?').upper()
        
        # Seleccionamos una ciudad al azar de la lista permitida
        ciudad_elegida = random.choice(CIUDADES_PERMITIDAS)
        
        # Construimos una dirección realista con esa ciudad
        direccion_completa = f"{fake.street_address()}, {fake.postcode()}, {ciudad_elegida}"

        menor = {
            "nombre": fake.first_name(),
            "apellidos": f"{fake.last_name()} {fake.last_name()}",
            "dni": dni,
            "fecha_nacimiento": fake.date_of_birth(minimum_age=5, maximum_age=17).strftime("%Y-%m-%d"),
            "direccion": direccion_completa, # <--- AQUI USAMOS LA NUEVA DIRECCION
            "url_foto": "https://storage.googleapis.com/foto-placeholder.jpg",
            "discapacidad": random.choice([True, False, False])
        }

        try:
            # Enviamos a la API
            resp = requests.post(f"{API_URL}/menores", json=menor)
            
            if resp.status_code == 201 or resp.status_code == 200:
                print(f"[{i+1}/{CANTIDAD}] [OK] Creado: {menor['nombre']} ({ciudad_elegida})")
                lista_memoria.append(menor)
            else:
                print(f"[{i+1}/{CANTIDAD}] [ERROR {resp.status_code}] API rechazó: {resp.text}")

        except requests.exceptions.ConnectionError:
            print(f"[{i+1}/{CANTIDAD}] [ERROR CRÍTICO] No conecta a {API_URL}.")
        except Exception as e:
            print(f"[{i+1}/{CANTIDAD}] [ERROR] Excepción: {e}")

    # Guardamos el JSON
    if lista_memoria:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(lista_memoria, f, indent=4, ensure_ascii=False)
        print(f"\n--- ÉXITO: Datos guardados en {ARCHIVO_SALIDA} ---")

if __name__ == "__main__":
    generar()