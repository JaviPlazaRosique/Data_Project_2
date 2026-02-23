from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from datetime import date
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text
from google.cloud import pubsub_v1, storage 
from uuid import UUID, uuid4
import os
import json
import logging

proyecto_region_instancia = os.getenv("PROYECTO_REGION_INSTANCIA")
usuario_db = os.getenv("USUARIO_DB")
contr_db = os.getenv("CONTR_DB")
nombre_bd = os.getenv("NOMBRE_BD")
id_proyecto = os.getenv("ID_PROYECTO")
topico_ubicaciones = os.getenv("TOPICO_UBICACIONES")
bucket_fotos = os.getenv("BUCKET_FOTOS")
api_key_seguridad = os.getenv("API_KEY")
contr_usuario_datastream = os.getenv("CONTR_USUARIO_DATASTREAM")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

publisher = pubsub_v1.PublisherClient()
if topico_ubicaciones and topico_ubicaciones.startswith("projects/"):
    topic_path = topico_ubicaciones
else:
    topic_path = publisher.topic_path(id_proyecto, topico_ubicaciones)
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_fotos)

conector = Connector()

def conexion_db():
    conexion =  conector.connect(
        proyecto_region_instancia, 
        "pg8000",
        user = usuario_db,
        password = contr_db,
        db = nombre_bd,
        ip_type = IPTypes.PRIVATE
    )
    return conexion 

engine = create_engine(
    "postgresql+pg8000://", 
    creator = conexion_db
)

class Menores(BaseModel):
    id: UUID = Field(default_factory = uuid4)
    id_adulto: UUID
    nombre: str
    apellidos: str
    dni: str
    fecha_nacimiento: date
    direccion: str
    url_foto: str
    discapacidad: bool

class Adultos(BaseModel):
    id: UUID = Field(default_factory = uuid4)
    nombre: str
    apellidos: str
    telefono: str
    email: str
    ciudad: str
    clave: str

class ZonasRestringidas(BaseModel):
    id: UUID = Field(default_factory = uuid4)
    id_menor: UUID
    nombre: str
    latitud: float
    longitud: float
    radio_peligro: int
    radio_advertencia: int

class Ubicaciones(BaseModel):
    id_menor: str
    timestamp: str
    latitud: float
    longitud: float

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == api_key_seguridad:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No se pudo validar las credenciales"
    )

app = FastAPI(dependencies=[Depends(get_api_key)])

def crear_tablas():
    logger.info("Iniciando la creación y configuración de tablas en la base de datos...")
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        logger.info("Creando extensión uuid-ossp si no existe...")
        conn.execute(text("""
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """))
        logger.info("Creando tabla adultos si no existe...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS adultos (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                nombre VARCHAR(100) NOT NULL,
                apellidos VARCHAR(100),
                telefono VARCHAR(20), 
                email VARCHAR(100),
                ciudad VARCHAR(100),
                clave VARCHAR(100)
            );
        """))
        logger.info("Creando tabla menores si no existe...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS menores (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                id_adulto UUID REFERENCES adultos(id),
                nombre VARCHAR(100),
                apellidos VARCHAR(100),
                dni VARCHAR(50),
                fecha_nacimiento DATE,
                direccion VARCHAR(100),
                url_foto VARCHAR(255),
                discapacidad BOOLEAN
            );
        """))
        logger.info("Creando tabla zonas_restringidas si no existe...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS zonas_restringidas (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                id_menor UUID REFERENCES menores(id),
                nombre VARCHAR(100),
                latitud DOUBLE PRECISION NOT NULL,
                longitud DOUBLE PRECISION NOT NULL,
                radio_peligro INTEGER,
                radio_advertencia INTEGER
            );
        """))
        logger.info("Creando tabla historico_notificaciones si no existe...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_notificaciones (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                id_menor UUID REFERENCES menores(id),
                nombre_menor VARCHAR(100),
                latitud DOUBLE PRECISION NOT NULL,
                longitud DOUBLE PRECISION NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                estado VARCHAR(20)
            );
        """))
        logger.info("Configurando usuario de replicación y permisos...")
        try:
            conn.execute(text(f'ALTER USER "{usuario_db}" WITH REPLICATION;'))
        except Exception as e:
            logger.warning(f"No se pudo asignar el rol REPLICATION al usuario '{usuario_db}': {e}")
        user_exists = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'usuario_datastream'")).fetchone()
        if not user_exists:
            conn.execute(text(f"CREATE USER usuario_datastream WITH REPLICATION IN ROLE cloudsqlsuperuser LOGIN PASSWORD '{contr_usuario_datastream}';"))
        conn.execute(text(f'GRANT CONNECT ON DATABASE "{nombre_bd}" TO usuario_datastream;'))
        conn.execute(text("GRANT USAGE ON SCHEMA public TO usuario_datastream;"))
        conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA public TO usuario_datastream;"))
        conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO usuario_datastream;"))
        logger.info("Configurando publicación y slot de replicación...")
        pub_exists = conn.execute(text("SELECT 1 FROM pg_publication WHERE pubname = 'datastream_publication'")).fetchone()
        if not pub_exists:
            conn.execute(text("CREATE PUBLICATION datastream_publication FOR ALL TABLES;"))
        slot_exists = conn.execute(text("SELECT 1 FROM pg_replication_slots WHERE slot_name = 'datastream_slot'")).fetchone()
        if not slot_exists:
            conn.execute(text("SELECT pg_create_logical_replication_slot('datastream_slot', 'pgoutput')"))
    logger.info("Proceso de creación de tablas finalizado correctamente.")

@app.on_event("startup")
def startup_event():
    try:
        crear_tablas()
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")

def obtener_conexion():
    with engine.begin() as conexion:
        yield conexion

@app.post("/menores", status_code = 201)
async def crear_menor(menor: Menores, db = Depends(obtener_conexion)):
    try:
        consulta = text("""
            INSERT INTO menores (id, id_adulto, nombre, apellidos, dni, fecha_nacimiento, direccion, url_foto, discapacidad)
            VALUES (:id, :id_adulto, :nombre, :apellidos, :dni, :fecha_nacimiento, :direccion, :url_foto, :discapacidad)
        """)

        db.execute(consulta, menor.model_dump())

        return {"mensaje": "Menor creado exitosamente"}
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error al insertar: {str(e)}")

@app.post("/fotos_menores", status_code = 201)
async def crear_fotos_menores(id_menor: UUID, archivo: UploadFile = File(...)):
    try:
        archivo_bytes = await archivo.read()

        blob = bucket.blob(f"{id_menor}.png")

        blob.upload_from_string(archivo_bytes, content_type = archivo.content_type)
        return {
            "message": "Archivo ingerido correctamente",
            "url": f"https://console.cloud.google.com/storage/browser/{bucket_fotos}/{id_menor}.png"
        }
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error al subir la imagen: {str(e)}")

@app.get("/menores/id_direccion")
async def obtener_ids_menores(db = Depends(obtener_conexion)):
    try:
        consulta = text("""SELECT id, direccion FROM menores""")

        resultado = db.execute(consulta)

        menores = [{"id": row[0], "direccion": row[1]} for row in resultado]

        return {"menores": menores}
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error al obtener IDs: {str(e)}")

@app.post("/adultos", status_code = 201)
async def crear_adulto(adulto: Adultos, db = Depends(obtener_conexion)):
    try:
        consulta = text("""
            INSERT INTO adultos (id, nombre, apellidos, telefono, email, ciudad, clave)
            VALUES (:id, :nombre, :apellidos, :telefono, :email, :ciudad, :clave)
        """)

        db.execute(consulta, adulto.model_dump())

        return {"mensaje": "Adulto creado exitosamente"}

    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error al insertar: {str(e)}")

@app.post("/zonas_restringidas", status_code = 201)
async def crear_zona_restringida(zona: ZonasRestringidas, db = Depends(obtener_conexion)):
    try:
        consulta = text("""
            INSERT INTO zonas_restringidas (id, id_menor, nombre, latitud, longitud, radio_peligro, radio_advertencia)
            VALUES (:id, :id_menor, :nombre, :latitud, :longitud, :radio_peligro, :radio_advertencia)
        """)

        db.execute(consulta, zona.model_dump())

        return {"mensaje": "Zona restringida creada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error al insertar: {str(e)}")
    
@app.post("/ubicaciones", status_code = 201)
async def crear_ubicaciones(ubicacion: Ubicaciones):
    try: 
        mensaje_bytes = json.dumps(ubicacion.model_dump()).encode("utf-8")

        future = publisher.publish(topic_path, mensaje_bytes)

        mensaje_id = future.result()

        return {"mensaje": f"Ubicacion creada: {mensaje_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al publicar en Pub/Sub: {str(e)}")