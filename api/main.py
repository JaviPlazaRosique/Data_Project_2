from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import date
import os
import json

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

@app.get("/menores")