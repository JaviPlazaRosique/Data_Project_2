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
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<h1 style='text-align: center;'>Inicio de Sesión</h1>", unsafe_allow_html=True)

        if st.session_state.intentos > 0:
            with st.form("login_form"):
                nombre = st.text_input("Nombre")
                apellidos = st.text_input("Apellidos")
                telefono = st.text_input("Teléfono", type="password")
                
                c1, c2 = st.columns([3, 1])
                with c2:
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
        st.session_state.selected_child = None
        st.rerun()

    if "selected_child" not in st.session_state:
        st.session_state.selected_child = None

    menores = obtener_menores(st.session_state.usuario.id)

    if not menores:
        st.warning("Este usuario no tiene hijos.")
    elif st.session_state.selected_child is None:
        st.markdown("<h2 style='text-align: center;'>Mis Hijos</h2>", unsafe_allow_html=True)
        cols = st.columns(2)
        for idx, menor in enumerate(menores):
            with cols[idx % 2]:
                try:
                    nombre_archivo = menor.url_foto.split("/")[-1]
                    blob = bucket.blob(nombre_archivo)
                    datos_imagen = blob.download_as_bytes()
                    st.image(datos_imagen, use_container_width=True)
                except Exception as e:
                    st.error(f"Error cargando foto")
                
                if st.button(menor.nombre, key=f"btn_{menor.id}", use_container_width=True):
                    st.session_state.selected_child = menor
                    st.rerun()
    else:
        menor = st.session_state.selected_child
        if st.button("← Volver"):
            st.session_state.selected_child = None
            st.rerun()

        st.title(menor.nombre)
        
        col_foto, col_datos = st.columns([1, 3])
        
        with col_foto:
            try:
                nombre_archivo = menor.url_foto.split("/")[-1]
                blob = bucket.blob(nombre_archivo)
                datos_imagen = blob.download_as_bytes()
                st.image(datos_imagen, use_container_width=True)
            except:
                pass

        with col_datos:
            st.write(f"**DNI:** {menor.dni}")
            st.write(f"**Fecha Nacimiento:** {menor.fecha_nacimiento}")
            st.write(f"**Dirección:** {menor.direccion}")
            if menor.discapacidad:
                st.write("**Discapacidad:** Sí")

        st.subheader("Mapa")
        zonas = obtener_zonas_restringidas(menor.id)
        
        lat, lon = 39.4699, -0.3763 
        direccion_lower = str(menor.direccion).lower()
        
        if "madrid" in direccion_lower:
            lat, lon = 40.4168, -3.7038
        elif "barcelona" in direccion_lower:
            lat, lon = 41.3851, 2.1734
        
        m = folium.Map(location=[lat, lon], zoom_start=12, tiles=None)
        
        folium.TileLayer("OpenStreetMap", name="Callejero").add_to(m)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite'
        ).add_to(m)

        folium.TileLayer(
            tiles='cartodbdark_matter',
            name='Modo Oscuro'
        ).add_to(m)

        folium.LayerControl().add_to(m)

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
        
        st_folium(m, use_container_width=True, height=500, key=f"mapa_{menor.id}")
