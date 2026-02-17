import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

def main():
    st.set_page_config(page_title="Mapa de Ubicaciones", layout="wide")
    
    st.title("Mapa de Ubicaciones")
    
    # Datos de ejemplo basados en las ciudades del proyecto
    data = {
        'Ciudad': ['Madrid', 'Barcelona', 'Valencia'],
        'Latitud': [40.4168, 41.3851, 39.4699],
        'Longitud': [-3.7038, 2.1734, -0.3763]
    }
    
    df = pd.DataFrame(data)
    
    # Crear mapa centrado en España
    m = folium.Map(location=[40.4637, -3.7492], zoom_start=6)
    
    # Añadir marcadores al mapa
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=row['Ciudad'],
            tooltip=row['Ciudad']
        ).add_to(m)
    
    # Mostrar el mapa usando streamlit-folium
    st_folium(m, width=1000, height=600)

if __name__ == "__main__":
    main()