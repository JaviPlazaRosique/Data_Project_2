import json
import requests
import random
from faker import Faker

# --- CONFIGURACION ---
API_URL = "http://localhost:8000/api/v1/zonas-restringidas"
ARCHIVO_SALIDA = "datos_zonas.json"
CANTIDAD = 5

fake = Faker('es_ES')

def generar():
    lista_zonas = []
    print(f"Generando {CANTIDAD} zonas restringidas...")

    # 1. GENERAR DATOS EN MEMORIA
    for _ in range(CANTIDAD):
        
        # Logica: El radio de advertencia debe ser mayor que el de peligro
        r_peligro = random.randint(20, 100)
        r_advertencia = r_peligro + random.randint(20, 50)

        # Estructura segun tu tabla SQL
        # Nota: No enviamos 'id' porque es SERIAL (autoincremental)
        zona = {
            "nombre": f"Zona {fake.word().capitalize()} - {fake.city()}",
            "latitud": float(fake.latitude()),
            "longitud": float(fake.longitude()),
            "radio_peligro": r_peligro,
            "radio_advertencia": r_advertencia
        }
        
        lista_zonas.append(zona)

    # 2. GUARDAR EN DISCO (SEGURIDAD)
    try:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(lista_zonas, f, indent=4, ensure_ascii=False)
        print(f"GUARDADO SEGURO: {len(lista_zonas)} zonas en {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"ERROR critico guardando archivo: {e}")
        return

    # # 3. ENVIAR A LA API
    # print(f"Iniciando envio a la API ({API_URL})...")

    # for item in lista_zonas:
    #     try:
    #         r = requests.post(API_URL, json=item, timeout=2)
    #         if r.status_code == 200 or r.status_code == 201:
    #             print(f"[API] Zona creada: {item['nombre']}")
    #         else:
    #             print(f"[API Error] {r.status_code}: {r.text}")
    #     except Exception:
    #         pass # Si falla la conexion, los datos ya estan guardados

    # print("Proceso finalizado.")

if __name__ == "__main__":
    generar()