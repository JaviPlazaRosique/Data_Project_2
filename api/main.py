from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import date
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text
import os
import json

proyecto_region_instancia = os.getenv("PROYECTO_REGION_INSTANCIA")
usuario_db = os.getenv("USUARIO_DB")
contr_db = os.getenv("CONTR_DB")
nombre_bd = os.getenv("NOMBRE_BD")

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

class HistoricoUbicaciones(BaseModel):
    id_menor: int
    latitud: float
    longitud: float
    radio: int
    fecha: date
    duracion: int

class ZonasRestringidas(BaseModel):
    nombre: str
    latitud: float
    longitud: float
    radio_peligro: int
    radio_advertencia: int

app = FastAPI()

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

@app.post("/historico_ubicaciones", status_code = 201)
async def crear_historico_ubicacion(historico: HistoricoUbicaciones, db = Depends(obtener_conexion)):
    try:
        consulta = text("""
            INSERT INTO historico_ubicaciones (id_menor, latitud, longitud, radio, fecha, duracion)
            VALUES (:id_menor, :latitud, :longitud, :radio, :fecha, :duracion)
        """)

        db.execute(consulta, historico.model_dump())

        return {"mensaje": "Histórico de ubicación creado exitosamente"}

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
