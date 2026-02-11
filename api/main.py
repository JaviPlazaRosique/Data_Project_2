from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from datetime import date
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text
from google.cloud import pubsub_v1, storage
from uuid import UUID, uuid4 
import os
import json

proyecto_region_instancia = os.getenv("PROYECTO_REGION_INSTANCIA")
usuario_db = os.getenv("USUARIO_DB")
contr_db = os.getenv("CONTR_DB")
nombre_bd = os.getenv("NOMBRE_BD")
id_proyecto = os.getenv("ID_PROYECTO")
topico_ubicaciones = os.getenv("TOPICO_UBICACIONES")
bucket_fotos = os.getenv("BUCKET_FOTOS")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(id_proyecto, topico_ubicaciones)

storage_client = storage.Client()
bucket = storage_client.bucket(bucket_fotos)

conector = Connector()

def conexion_db():
    conexion =  conector.connect(
        proyecto_region_instancia, 
        "psycopg",
        user = usuario_db,
        password = contr_db,
        db = nombre_bd,
        ip_type = IPTypes.PRIVATE
    )
    return conexion 

engine = create_engine(
    "postgresql+psycopg2://", 
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

class ZonasRestringidas(BaseModel):
    id: UUID = Field(default_factory = uuid4)
    id_menor: UUID
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

app = FastAPI()

def obtener_conexion():
    with engine.begin() as conexion:
        yield conexion

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

@app.post("/adultos", status_code = 201)
async def crear_adulto(adulto: Adultos, db = Depends(obtener_conexion)):
    try:
        consulta = text("""
            INSERT INTO adultos (id, nombre, apellidos, telefono, email)
            VALUES (:id, :nombre, :apellidos, :telefono, :email)
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

@app.post("/historico_ubicaciones", status_code = 201)
async def crear_historico_ubicacion(ubicacion: HistoricoUbicaciones, db = Depends(obtener_conexion)):
    try: 
        consulta = text("""
            INSERT INTO historico_ubicaciones (id, id_menor, latitud, longitud, radio, fecha, duracion, estado)
            VALUES (:id, :id_menor, :latitud, :longitud, :radio, :fecha, :duracion, :estado)
        """)

        db.execute(consulta, ubicacion.model_dump())

        return {"mensaje": "Historico de ubicación creado exitosamente"}
    except Exception as e: 
        raise HTTPException(status_code = 500, detail = f"Error al insertar: {str(e)}")

@app.post("/ubicaciones", status_code = 201)
async def crear_ubicaciones(ubicacion):
    try: 
        mensaje_bytes = json.dumps(ubicacion.model_dump()).encode("utf-8")

        future = publisher.publish(topic_path, mensaje_bytes)

        mensaje_id = future.result()

        return {"mensaje": f"Ubicacion creada: {mensaje_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al publicar en Pub/Sub: {str(e)}")
