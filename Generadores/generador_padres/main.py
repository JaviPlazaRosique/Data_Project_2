import json
import requests
import os
import random
from faker import Faker
from sqlalchemy import create_engine, text
from google.cloud.sql.connector import Connector, IPTypes

# --- CONFIGURACIÓN DE ENTORNO ---
# Leemos la variable de entorno API_URL (para Docker).
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Archivos de entrada y salida
ARCHIVO_ENTRADA = "memoria_ninos.json"
ARCHIVO_SALIDA = "memoria_padres.json"

# --- CONFIGURACIÓN BASE DE DATOS (Necesaria para buscar el ID del hijo) ---
PROYECTO = os.getenv("PROYECTO_REGION_INSTANCIA", "tu-proyecto:region:instancia")
USER_DB = os.getenv("USUARIO_DB", "postgres")
PASS_DB = os.getenv("CONTR_DB", "tu_contraseña")
NAME_DB = os.getenv("NOMBRE_BD", "tu_base_datos")

fake = Faker('es_ES')

# --- FUNCIÓN AUXILIAR: CONEXIÓN A BD ---
def obtener_id_por_dni(dni_buscado):
    """Busca en la BD el ID autogenerado del niño usando su DNI"""
    try:
        conector = Connector()
        def getconn():
            return conector.connect(
                PROYECTO, "pg8000", user=USER_DB, password=PASS_DB, db=NAME_DB, ip_type=IPTypes.PUBLIC
            )
        
        # Creamos el motor temporalmente
        engine = create_engine("postgresql+pg8000://", creator=getconn)
        
        with engine.connect() as conn:
            query = text("SELECT id FROM menores WHERE dni = :dni")
            result = conn.execute(query, {"dni": dni_buscado}).fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"[ERROR BD] No se pudo obtener ID: {e}")
        return None

# --- FUNCIÓN PRINCIPAL ---
def generar():
    lista_memoria = []
    
    # 1. Cargamos el fichero de niños
    try:
        with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
            ninos = json.load(f)
        print(f"--- 1. Leídos {len(ninos)} niños del archivo local ---")
    except FileNotFoundError:
        print(f"[ERROR] No encuentro {ARCHIVO_ENTRADA}. Ejecuta primero el script de niños.")
        return

    print(f"--- 2. Generando Padres y conectando a: {API_URL}/padres ---")

    for i, nino in enumerate(ninos):
        dni_nino = nino['dni']
        
        # Obtenemos el ID real (Foreign Key)
        id_real = obtener_id_por_dni(dni_nino)

        if id_real:
            # Generamos datos según la tabla 'padres'
            padre = {
                "nombre": fake.first_name(),
                "apellidos": nino['apellidos'], # Usamos los mismos apellidos para dar realismo
                "telefono": fake.phone_number().replace(" ", "")[:15],
                "id_menor": id_real,            # <--- CLAVE FORÁNEA
                "email": fake.email()
            }

            try:
                # Enviamos a la API (Asegúrate de que tu endpoint sea /padres o /adultos)
                resp = requests.post(f"{API_URL}/padres", json=padre)
                
                if resp.status_code == 201 or resp.status_code == 200:
                    print(f"[{i+1}/{len(ninos)}] [OK] Padre creado para niño ID {id_real}")
                    lista_memoria.append(padre)
                else:
                    print(f"[{i+1}/{len(ninos)}] [ERROR {resp.status_code}] API rechazó: {resp.text}")

            except requests.exceptions.ConnectionError:
                print(f"[{i+1}/{len(ninos)}] [ERROR CRÍTICO] No conecta a la API.")
            except Exception as e:
                print(f"[{i+1}/{len(ninos)}] [ERROR] Excepción: {e}")
        else:
            print(f"[{i+1}/{len(ninos)}] [SALTADO] El niño con DNI {dni_nino} no está en la BD.")

    # Guardamos el JSON
    if lista_memoria:
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(lista_memoria, f, indent=4, ensure_ascii=False)
        print(f"\n--- ÉXITO: {len(lista_memoria)} padres guardados en {ARCHIVO_SALIDA} ---")

if __name__ == "__main__":
    generar()