import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text
import os
from google.cloud import storage, firestore
import uuid

proyecto_region_instancia = os.getenv("PROYECTO_REGION_INSTANCIA")
usuario_db = os.getenv("USUARIO_DB")
contr_db = os.getenv("CONTR_DB")
nombre_bd = os.getenv("NOMBRE_BD")
bucket_fotos = os.getenv("BUCKET_FOTOS")

storage_client = storage.Client()
bucket = storage_client.bucket(bucket_fotos)
db_firestore = firestore.Client()

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

if "registering" not in st.session_state:
    st.session_state.registering = False

def verificar_credenciales(nombre, apellidos, clave):
    with engine.connect() as conn:
        consulta = text("""
            SELECT * FROM adultos 
            WHERE nombre = :nombre AND apellidos = :apellidos AND clave = :clave
        """)
        resultado = conn.execute(consulta, {"nombre": nombre, "apellidos": apellidos, "clave": clave}).fetchone()
        return resultado

def registrar_adulto(nombre, apellidos, telefono, email, clave):
    try:
        with engine.begin() as conn:
            consulta = text("""
                INSERT INTO adultos (nombre, apellidos, telefono, email, clave)
                VALUES (:nombre, :apellidos, :telefono, :email, :clave)
            """)
            conn.execute(consulta, {"nombre": nombre, "apellidos": apellidos, "telefono": telefono, "email": email, "clave": clave})
        return True
    except Exception as e:
        return False

def registrar_menor(id_adulto, nombre, apellidos, dni, fecha_nacimiento, direccion, discapacidad, archivo_foto):
    try:
        new_id = str(uuid.uuid4())
        url_foto = ""
        
        if archivo_foto:
            blob = bucket.blob(f"{new_id}.png")
            blob.upload_from_file(archivo_foto, content_type=archivo_foto.type)
            url_foto = f"https://storage.googleapis.com/{bucket_fotos}/{new_id}.png"
            
        with engine.begin() as conn:
            consulta = text("""
                INSERT INTO menores (id, id_adulto, nombre, apellidos, dni, fecha_nacimiento, direccion, url_foto, discapacidad)
                VALUES (:id, :id_adulto, :nombre, :apellidos, :dni, :fecha_nacimiento, :direccion, :url_foto, :discapacidad)
            """)
            conn.execute(consulta, {
                "id": new_id, "id_adulto": id_adulto, "nombre": nombre, "apellidos": apellidos, "dni": dni, 
                "fecha_nacimiento": fecha_nacimiento, "direccion": direccion, "url_foto": url_foto, "discapacidad": discapacidad
            })
        return True
    except Exception as e:
        return False

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

def obtener_ubicacion_menor(id_menor):
    try:
        doc_ref = db_firestore.collection("ubicaciones").document(str(id_menor))
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception:
        return None

def obtener_historico_notificaciones(id_menor):
    try:
        with engine.connect() as conn:
            consulta = text("SELECT fecha, estado, latitud, longitud FROM historico_notificaciones WHERE id_menor = :id_menor ORDER BY fecha DESC")
            df = pd.read_sql(consulta, conn, params={"id_menor": id_menor})
            return df
    except Exception:
        return pd.DataFrame()

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.session_state.registering:
            st.markdown("<h1 style='text-align: center;'>Registro de Nuevo Padre</h1>", unsafe_allow_html=True)
            with st.form("register_form"):
                nombre = st.text_input("Nombre")
                apellidos = st.text_input("Apellidos")
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
                clave = st.text_input("Clave", type="password")
                submit_registro = st.form_submit_button("Registrarse")

                if submit_registro:
                    if registrar_adulto(nombre, apellidos, telefono, email, clave):
                        st.success("Registro completado con éxito. Por favor, inicia sesión.")
                        st.session_state.registering = False
                        st.rerun()
                    else:
                        st.error("Error al registrar el usuario.")
            
            if st.button("Volver al Inicio de Sesión"):
                st.session_state.registering = False
                st.rerun()

        else:
            st.markdown("<h1 style='text-align: center;'>Inicio de Sesión</h1>", unsafe_allow_html=True)

            if st.session_state.intentos > 0:
                with st.form("login_form"):
                    nombre = st.text_input("Nombre")
                    apellidos = st.text_input("Apellidos")
                    clave = st.text_input("Clave", type="password")
                    
                    c1, c2 = st.columns([3, 1])
                    with c2:
                        submit = st.form_submit_button("Entrar")

                    if submit:
                        usuario = verificar_credenciales(nombre.strip(), apellidos.strip(), clave.strip())
                        if usuario:
                            st.session_state.logged_in = True
                            st.session_state.usuario = usuario
                            st.success("Bienvenido!")
                            st.rerun()
                        else:
                            st.session_state.intentos -= 1
                            st.error(f"Credenciales incorrectas. Intentos restantes: {st.session_state.intentos}")
                
                st.markdown("---")
                if st.button("¿No tienes cuenta? Regístrate aquí"):
                    st.session_state.registering = True
                    st.rerun()
            else:
                st.error("Has superado el número de intentos permitidos.")

else:
    st.sidebar.write(f"Usuario: {st.session_state.usuario.nombre} {st.session_state.usuario.apellidos}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.intentos = 3
        st.session_state.selected_child = None
        st.rerun()

    @st.fragment(run_every=5)
    def verificar_alertas_globales():
        try:
            menores_usuario = obtener_menores(st.session_state.usuario.id)
            ids_menores = [str(m.id) for m in menores_usuario]
            
            if ids_menores:
                for i in range(0, len(ids_menores), 10):
                    chunk = ids_menores[i:i+10]
                    docs = db_firestore.collection("notificaciones")\
                        .where("id_menor", "in", chunk)\
                        .where("leido", "==", False)\
                        .stream()
                    
                    for doc in docs:
                        data = doc.to_dict()
                        st.toast(f"{data.get('asunto')}: {data.get('cuerpo')}", icon="🚨")
                        db_firestore.collection("notificaciones").document(doc.id).update({"leido": True})
        except Exception:
            pass

    verificar_alertas_globales()

    if "selected_child" not in st.session_state:
        st.session_state.selected_child = None

    if "adding_child" not in st.session_state:
        st.session_state.adding_child = False

    if st.session_state.adding_child:
        st.markdown("<h2 style='text-align: center;'>Registrar Nuevo Menor</h2>", unsafe_allow_html=True)
        if st.button("← Volver"):
            st.session_state.adding_child = False
            st.rerun()

        with st.form("form_alta_menor"):
            nombre = st.text_input("Nombre")
            apellidos = st.text_input("Apellidos")
            dni = st.text_input("DNI")
            fecha_nacimiento = st.date_input("Fecha de Nacimiento")
            direccion = st.text_input("Dirección")
            discapacidad = st.checkbox("¿Tiene discapacidad?")
            foto = st.file_uploader("Foto del menor", type=["png", "jpg", "jpeg"])
            
            submit_nuevo_menor = st.form_submit_button("Guardar")
            
            if submit_nuevo_menor:
                if registrar_menor(st.session_state.usuario.id, nombre, apellidos, dni, fecha_nacimiento, direccion, discapacidad, foto):
                    st.success("Menor registrado correctamente")
                    st.session_state.adding_child = False
                    st.rerun()
                else:
                    st.error("Error al registrar el menor")

    elif st.session_state.selected_child is None:
        menores = obtener_menores(st.session_state.usuario.id)
        
        col_tit, col_btn = st.columns([3, 1])
        with col_tit:
            st.markdown("<h2 style='text-align: center;'>Mis Hijos</h2>", unsafe_allow_html=True)
        with col_btn:
            if st.button("➕ Añadir Menor"):
                st.session_state.adding_child = True
                st.rerun()

        if not menores:
            st.warning("Este usuario no tiene hijos.")
        else:
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

        tab_mapa, tab_historico = st.tabs(["Mapa en Tiempo Real", "Histórico de Alertas"])

        with tab_mapa:
            st.subheader("Mapa")
            zonas = obtener_zonas_restringidas(menor.id)
            
            @st.fragment(run_every=5)
            def mostrar_mapa():
                ubicacion = obtener_ubicacion_menor(menor.id)
                
                lat_map, lon_map = 39.4699, -0.3763 
                zoom_map = 12
                
                map_key = f"mapa_{menor.id}"
                map_state = st.session_state.get(map_key)
                
                if map_state and map_state.get("center"):
                    lat_map = map_state["center"]["lat"]
                    lon_map = map_state["center"]["lng"]
                    zoom_map = map_state["zoom"]
                elif ubicacion:
                    lat_map, lon_map = ubicacion['latitud'], ubicacion['longitud']
                else:
                    direccion_lower = str(menor.direccion).lower()
                    
                    if "madrid" in direccion_lower:
                        lat_map, lon_map = 40.4168, -3.7038
                    elif "barcelona" in direccion_lower:
                        lat_map, lon_map = 41.3851, 2.1734
                    
                m = folium.Map(location=[lat_map, lon_map], zoom_start=zoom_map, tiles=None)
                
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

                if ubicacion:
                    estado = ubicacion.get('estado', 'OK')
                    color_marcador = "green"
                    if estado == "PELIGRO":
                        color_marcador = "red"
                    elif estado == "ADVERTENCIA":
                        color_marcador = "orange"
                    
                    folium.Marker(
                        location=[ubicacion['latitud'], ubicacion['longitud']],
                        popup=f"Ubicación Actual ({estado})",
                        icon=folium.Icon(color=color_marcador, icon="user")
                    ).add_to(m)

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
                
                st_folium(m, use_container_width=True, height=500, key=map_key)

            mostrar_mapa()

        with tab_historico:
            st.subheader("Historial de Notificaciones")
            df_notificaciones = obtener_historico_notificaciones(menor.id)
            
            if not df_notificaciones.empty:
                st.write("Selecciona una notificación para ver el detalle en el mapa:")
                event = st.dataframe(
                    df_notificaciones, 
                    use_container_width=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    hide_index=True
                )
                
                if event.selection["rows"]:
                    idx = event.selection["rows"][0]
                    row = df_notificaciones.iloc[idx]
                    
                    st.subheader("Ubicación de la Alerta")
                    m_hist = folium.Map(location=[row['latitud'], row['longitud']], zoom_start=15)
                    color = "red" if row['estado'] == "PELIGRO" else "orange"
                    folium.Marker(
                        [row['latitud'], row['longitud']],
                        popup=f"{row['estado']} - {row['fecha']}",
                        icon=folium.Icon(color=color, icon="info-sign")
                    ).add_to(m_hist)
                    st_folium(m_hist, height=300, use_container_width=True, key="mapa_historico")
            else:
                st.info("No hay notificaciones registradas para este menor.")
