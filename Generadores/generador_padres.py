import json
import requests
from faker import Faker

# --- CONFIGURACION ---
API_URL = "http://localhost:8000/api/v1/adultos"
ARCHIVO_ENTRADA = "memoria_ninos.json"    # Leemos los ninos creados
ARCHIVO_SALIDA = "datos_adultos.json"     # Guardamos los adultos aqui

fake = Faker('es_ES')

def generar():
    # 1. CARGAR DATOS DE NINOS
    try:
        with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
            datos_ninos = json.load(f)
    except FileNotFoundError:
        print("ERROR: Primero ejecuta el script de ninos.")
        return

    lista_adultos = []
    print(f"Generando padres para {len(datos_ninos)} ninos...")

    # 2. GENERAR LA LISTA EN MEMORIA
    for nino in datos_ninos:
        # Estructura EXACTA para tu tabla SQL
        payload = {
            "id": nino['id_adulto'], # USAMOS EL ID QUE YA ASIGNAMOS AL NINO
            "nombre": fake.first_name(),
            "apellidos": nino['apellido'], # Mismo apellido
            "telefono": int(fake.phone_number().replace(" ", "")[-9:]),
            "email": fake.email(),
            "id_niño": nino['id'] # VINCULACION CLAVE
        }
        
        # Anadimos a la lista local
        lista_adultos.append(payload)

    # 3. GUARDAR EN DISCO (ANTES DE ENVIAR)
    try:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(lista_adultos, f, indent=4, ensure_ascii=False)
        print(f"GUARDADO SEGURO: {len(lista_adultos)} registros en {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"ERROR critico guardando archivo: {e}")
        return

    # # 4. ENVIAR A LA API
    # print(f"Iniciando envio a la API ({API_URL})...")

    # for item in lista_adultos:
    #     try:
    #         r = requests.post(API_URL, json=item)
    #         if r.status_code == 200 or r.status_code == 201:
    #             print(f"[API] Padre creado: {item['nombre']}")
    #         else:
    #             print(f"[API Error] {r.status_code}: {r.text}")
    #     except Exception as e:
    #         # Si falla la conexion, no pasa nada porque ya guardamos el archivo
    #         pass
            
    # print("Proceso finalizado.")

if __name__ == "__main__":
    generar()