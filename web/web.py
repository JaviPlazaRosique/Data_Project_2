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

def consulatar_adultos():
    """Realiza una consulta directa a la tabla adultos."""
    with engine.connect() as conn:
        query = text("SELECT * FROM adultos;")
        return pd.read_sql(query, conn)


def consultar_menores():
    """Realiza una consulta directa a la tabla menores."""
    with engine.connect() as conn:
        query = text("SELECT * FROM menores;")
        return pd.read_sql(query, conn)


def main():
    st.set_page_config(page_title="Mapa de Ubicaciones", layout="wide")
    
    st.title("Mapa de Ubicaciones")
    st.subheader("Consulta Directa a Base de Datos")
    if st.checkbox("Ver tabla de Menores"):
        try:
            df_menores = consultar_menores()
            st.dataframe(df_menores)
        except Exception as e:
            st.error(f"Error al consultar la base de datos: {e}")
    if st.checkbox("Ver tabla de Adultos"):
        try:
            df_adultos = consulatar_adultos()
            st.dataframe(df_adultos)
        except Exception as e: 
            st.error(f"Error al consultar la base de datos: {e}")

    data = {
        'Ciudad': ['Madrid', 'Barcelona', 'Valencia'],
        'Latitud': [40.4168, 41.3851, 39.4699],
        'Longitud': [-3.7038, 2.1734, -0.3763]
    }
    
    df = pd.DataFrame(data)
    
    m = folium.Map(location=[40.4637, -3.7492], zoom_start=6)
    
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=row['Ciudad'],
            tooltip=row['Ciudad']
        ).add_to(m)
    
    st_folium(m, width=1000, height=600)

if __name__ == "__main__":
    main()