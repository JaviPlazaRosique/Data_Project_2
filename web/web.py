import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text
import os
from google.cloud import storage

proyecto_region_instancia = os.getenv("PROYECTO_REGION_INSTANCIA")
usuario_db = os.getenv("USUARIO_DB")
contr_db = os.getenv("CONTR_DB")
nombre_bd = os.getenv("NOMBRE_BD")
bucket_fotos = os.getenv("BUCKET_FOTOS")

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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "intentos" not in st.session_state:
    st.session_state.intentos = 3

def verificar_credenciales(nombre, apellidos, telefono):
    with engine.connect() as conn:
        consulta = text("""
            SELECT * FROM adultos 
            WHERE nombre = :nombre AND apellidos = :apellidos AND telefono = :telefono
        """)
        resultado = conn.execute(consulta, {"nombre": nombre, "apellidos": apellidos, "telefono": telefono}).fetchone()
        return resultado

def obtener_menores(id_adulto):
    with engine.connect() as conn:
        consulta = text("SELECT * FROM menores WHERE id_adulto = :id_adulto")
        resultados = conn.execute(consulta, {"id_adulto": id_adulto}).fetchall()
        return resultados

def obtener_zonas_restringidas(id_menor):
    with engine.connect() as conn:
        consulta = text("SELECT * FROM zonas_restringidas WHERE id_menor = :id_menor")
        resultados = conn.execute(consulta, {"id_menor": id_menor}).fetchall()
        return resultados

if not st.session_state.logged_in:
    st.title("Inicio de Sesión")

    if st.session_state.intentos > 0:
        with st.form("login_form"):
            nombre = st.text_input("Nombre")
            apellidos = st.text_input("Apellidos")
            telefono = st.text_input("Teléfono")
            submit = st.form_submit_button("Entrar")

            if submit:
                usuario = verificar_credenciales(nombre.strip(), apellidos.strip(), telefono.strip())
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

    menores = obtener_menores(st.session_state.usuario.id)

    if menores:
        nombres_pestanas = ["Resumen"] + [f"{m.nombre} {m.apellidos}" for m in menores]
        tabs = st.tabs(nombres_pestanas)

        with tabs[0]:
            st.subheader("Mis Menores")
            cols = st.columns(len(menores))
            for idx, menor in enumerate(menores):
                with cols[idx]:
                    try:
                        nombre_archivo = menor.url_foto.split("/")[-1]
                        blob = bucket.blob(nombre_archivo)
                        datos_imagen = blob.download_as_bytes()
                        st.image(datos_imagen, caption=f"{menor.nombre} {menor.apellidos}", width=150)
                    except Exception as e:
                        st.error(f"Error cargando foto: {e}")

        # Pestañas individuales por menor
        for i, menor in enumerate(menores):
            with tabs[i + 1]:
                st.subheader(f"Mapa de {menor.nombre}")
                zonas = obtener_zonas_restringidas(menor.id)
                
                lat, lon = 39.4699, -0.3763 
                direccion_lower = str(menor.direccion).lower()
                
                if "madrid" in direccion_lower:
                    lat, lon = 40.4168, -3.7038
                elif "barcelona" in direccion_lower:
                    lat, lon = 41.3851, 2.1734
                
                m = folium.Map(location=[lat, lon], zoom_start=12)
                
                for zona in zonas:
                    folium.Circle(
                        location=[zona.latitud, zona.longitud],
                        radius=zona.radio_advertencia,
                        color="yellow",
                        fill=True,
                        fill_opacity=0.2,
                        popup=f"Advertencia: {zona.nombre}"
                    ).add_to(m)
                    
                    folium.Circle(
                        location=[zona.latitud, zona.longitud],
                        radius=zona.radio_peligro,
                        color="red",
                        fill=True,
                        fill_opacity=0.4,
                        popup=f"Peligro: {zona.nombre}"
                    ).add_to(m)
                
                st_folium(m, width=700, height=500, key=f"mapa_{menor.id}")
    else:
        st.warning("No se encontraron menores asociados a este usuario.")
