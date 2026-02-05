
import json
import uuid
import random 
import requests
from faker import Faker
from generador_ninos import ARCHIVO_TEMP
from datetime import datetime
#Configuración
API_URL="http://localhost:8000/api/v1/ubicaciones"

ARCHIVO_TEMP = "memoria_ninos.json"      # LEEMOS de aquí
ARCHIVO_SALIDA = "datos_ubicaciones.json"   # GUARDAMOS aquí#archivo para guardar

Ubicaciones=1 #ubicaciones por niño, es decir, obtenemos 5 ubicaciones

fake=Faker('es_ES') #genera los datos en español

def generar():
    try:
        with open(ARCHIVO_TEMP, 'r', encoding='utf-8') as f:
            datos_ninos = json.load(f)
    except FileNotFoundError:
        print("Primero ejecuta el script de niños.")
        return
    
    lista_ubicaciones=[]
    total_estimado = len(datos_ninos) * Ubicaciones
    print(f" Generando {total_estimado} puntos GPS ({Ubicaciones} por cada niño)...")

    for nino in datos_ninos:
        for _ in range(Ubicaciones):
            ubicacion={
                "id": str(uuid.uuid4()),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "latitud": str(fake.latitude()),
                "longitud": str(fake.longitude()),
                "radio": str(random.randint(10, 50)) + "m",
                "direccion": random.randint(0, 360),
                "duracion": "0min",
                "id_niño": nino['id'] # VINCULACIÓN CON EL NIÑO
            }

            print(f"Generando ubicación para {nino['nombre']} {nino['apellido']} (ID Niño: {nino['id']})")
            print(f"Ubicación: Lat {ubicacion['latitud']}, Lon {ubicacion['longitud']}, Radio {ubicacion['radio']}")

            lista_ubicaciones.append(ubicacion)

        try:
            with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
                json.dump(lista_ubicaciones, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f" Error al guardar archivo: {e}")
            return # Si no se puede guardar, paramos.
        
            #Enviamos a la API
#             try:
#                 r = requests.post(API_URL, json=ubicacion)
#                 if r.status_code == 200 or r.status_code == 201:
#                     print(f" [API] Ubicación enviada (Niño: {nino['nombre']})")
#                 else:
#                     print(f"[API Error] {r.status_code}: {r.text}")
#             except Exception as e:
#                 print(f"Error de conexión: {e}")

if __name__ == "__main__":
    generar()