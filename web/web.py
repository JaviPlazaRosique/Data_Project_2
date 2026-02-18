import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text
import os

proyecto_region_instancia = os.getenv("PROYECTO_REGION_INSTANCIA")
usuario_db = os.getenv("USUARIO_DB")
contr_db = os.getenv("CONTR_DB")
nombre_bd = os.getenv("NOMBRE_BD")

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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "intentos" not in st.session_state:
    st.session_state.intentos = 3

def verificar_credenciales(nombre, apellidos, telefono):
    with engine.connect() as conn:
        consulta = text("SELECT * FROM adultos")
        resultados = conn.execute(consulta).fetchall()
        for adulto in resultados:
            if adulto.nombre == nombre and adulto.apellidos == apellidos and adulto.telefono == telefono:
                return adulto
        return None

if not st.session_state.logged_in:
    st.title("Inicio de Sesión")

    if st.session_state.intentos > 0:
        with st.form("login_form"):
            nombre = st.text_input("Nombre")
            apellidos = st.text_input("Apellidos")
            telefono = st.text_input("Teléfono")
            submit = st.form_submit_button("Entrar")

            if submit:
                usuario = verificar_credenciales(nombre, apellidos, telefono)
                if usuario:
                    st.session_state.logged_in = True
                    st.session_state.usuario = usuario
                    st.success("Bienvenido!")
                    st.rerun()
                else:
                    st.session_state.intentos -= 1
                    st.error(f"Credenciales incorrectas. Intentos restantes: {st.session_state.intentos}")
    else:
        st.error("Has superado el número de intentos permitidos.")

else:
    st.sidebar.write(f"Usuario: {st.session_state.usuario.nombre} {st.session_state.usuario.apellidos}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.intentos = 3
        st.rerun()
