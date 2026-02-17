from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from datetime import date
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text
from google.cloud import pubsub_v1
import os
import json

proyecto_region_instancia = os.getenv("PROYECTO_REGION_INSTANCIA")
usuario_db = os.getenv("USUARIO_DB")
contr_db = os.getenv("CONTR_DB")
nombre_bd = os.getenv("NOMBRE_BD")
id_proyecto = os.getenv("ID_PROYECTO")
topico_ubicaciones = os.getenv("TOPICO_UBICACIONES")
bucket_fotos = os.getenv("BUCKET_FOTOS")
api_key_seguridad = os.getenv("API_KEY")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(id_proyecto, topico_ubicaciones)

conector = Connector()

def conexion_db():
    conexion =  conector.connect(
        proyecto_region_instancia, 
        "psycopg",
        user = usuario_db,
        password = contr_db,
        db = nombre_bd,
        ip_type = IPTypes.PUBLIC
    )
    return conexion 

engine = create_engine(
    "postgresql+psycopg2://", 
    creator = conexion_db
)

class Menores(BaseModel):
    nombre: str
    apellidos: str
    dni: str
    fecha_nacimiento: date
    direccion: str
    url_foto: str
    discapacidad: bool

class Adultos(BaseModel):
    nombre: str
    apellidos: str
    telefono: str
    id_menor: int
    email: str

class ZonasRestringidas(BaseModel):
    nombre: str
    latitud: float
    longitud: float
    radio_peligro: int
    radio_advertencia: int

class HistoricoUbicaciones(BaseModel):
    id: UUID = Field(default_factory = uuid4)
    id_menor: UUID
    nombre: str
    latitud: float
    longitud: float
    radio: int
    fecha: date
    duracion: int
    estado: str

class Ubicaciones(BaseModel):
    user_id: str
    timestamp: str
    latitude: float
    longitude: float
    node_id: int
    street_name: str
    road_type: str
    poi_name: str
    poi_type: str

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == api_key_seguridad:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No se pudo validar las credenciales"
    )

app = FastAPI(dependencies=[Depends(get_api_key)])

def obtener_conexion():
    with engine.begin() as conexion:
        yield conexion

@app.post("/menores", status_code = 201)
async def crear_menor(menor: Menores, db = Depends(obtener_conexion)):
    try:
        consulta = text("""
            INSERT INTO menores (nombre, apellidos, dni, fecha_nacimiento, direccion, url_foto, discapacidad)
            VALUES (:nombre, :apellidos, :dni, :fecha_nacimiento, :direccion, :url_foto, :discapacidad)
        """)

        db.execute(consulta, menor.model_dump())

        return {"mensaje": "Menor creado exitosamente"}
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error al insertar: {str(e)}")

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
            INSERT INTO adultos (nombre, apellidos, telefono, id_menor, email)
            VALUES (:nombre, :apellidos, :telefono, :id_menor, :email)
        """)

        db.execute(consulta, adulto.model_dump())

        return {"mensaje": "Adulto creado exitosamente"}

    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error al insertar: {str(e)}")

@app.post("/zonas_restringidas", status_code = 201)
async def crear_zona_restringida(zona: ZonasRestringidas, db = Depends(obtener_conexion)):
    try:
        consulta = text("""
            INSERT INTO zonas_restringidas (nombre, latitud, longitud, radio_peligro, radio_advertencia)
            VALUES (:nombre, :latitud, :longitud, :radio_peligro, :radio_advertencia)
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

        mensaje_id = future.results()

        return {"mensaje": f"Ubicacion creada: {mensaje_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al publicar en Pub/Sub: {str(e)}")
