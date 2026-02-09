import json
import requests
from faker import Faker

# --- CONFIGURACION ---
API_URL = "http://localhost:8000/api/v1/adultos"
ARCHIVO_ENTRADA = "memoria_ninos.json"    # Leemos los niños creados en el paso anterior
ARCHIVO_SALIDA = "datos_adultos.json"     # Guardamos los adultos aquí para respaldo

# Inicializamos Faker en español
fake = Faker('es_ES')

def generar():
    # 1. CARGAR DATOS DE NIÑOS
    try:
        with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
            datos_ninos = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: No se encontró {ARCHIVO_ENTRADA}. Ejecuta primero el script de generación de niños.")
        return

    lista_adultos = []
    print(f"Generando padres para {len(datos_ninos)} niños...")

    # 2. GENERAR LA LISTA EN MEMORIA
    for nino in datos_ninos:
        
        # Generamos un número de teléfono móvil español realista (empiezan por 6 o 7)
        # Faker a veces mete espacios o prefijos +34, los limpiamos.
        telefono_raw = fake.phone_number().replace(" ", "").replace("-", "").replace("+34", "")
        # Aseguramos que tomamos los últimos 9 dígitos
        telefono_limpio = int(telefono_raw[-9:]) if len(telefono_raw) >= 9 else 600000000

        payload = {
            "id": nino['id_adulto'],       # USAMOS EL ID QUE YA VINCULAMOS AL NIÑO
            "nombre": fake.first_name(),
            "apellidos": nino['apellido'], # Usamos el mismo apellido que el niño
            "telefono": telefono_limpio,   
            "email": fake.email(),
            "id_nino": nino['id']          # VINCULACION CLAVE (Foreign Key)
        }
        
        lista_adultos.append(payload)

    # 3. GUARDAR EN DISCO (COPIA DE SEGURIDAD)
    try:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(lista_adultos, f, indent=4, ensure_ascii=False)
        print(f"GUARDADO LOCAL: {len(lista_adultos)} registros en {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"ERROR crítico guardando archivo: {e}")
        return

    # # 4. ENVIAR A LA API
    # print(f"Iniciando envío a la API ({API_URL})...")

    # for item in lista_adultos:
    #     try:
    #         # Enviamos la petición POST
    #         r = requests.post(API_URL, json=item)
            
    #         if r.status_code == 200 or r.status_code == 201:
    #             print(f"[API OK] Padre creado: {item['nombre']} {item['apellidos']}")
    #         else:
    #             print(f"[API ERROR] Fallo al crear {item['nombre']}: {r.status_code} - {r.text}")
                
    #     except requests.exceptions.ConnectionError:
    #         print(f"[API FAIL] No se pudo conectar a {API_URL}. ¿Está encendido el servidor?")
    #         break # Paramos el bucle si el servidor está caído para no spamear errores
    #     except Exception as e:
    #         print(f"[ERROR] Excepción general: {e}")
            
    # print("Proceso finalizado.")

if __name__ == "__main__":
    generar()