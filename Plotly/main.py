import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import uuid
import os

# ==========================================================
# 1️⃣ GENERACIÓN DE DATOS (Simulación exacta de BQ)
# ==========================================================
def generate_bq_data():
    # Tabla: adultos
    adultos_ids = [str(uuid.uuid4()) for _ in range(5)]
    df_adultos = pd.DataFrame({
        "id": adultos_ids,
        "nombre": ["Carlos", "Ana", "Laura", "David", "María"]
    })

    # Tabla: menores
    menores_ids = [str(uuid.uuid4()) for _ in range(10)]
    df_menores = pd.DataFrame({
        "id": menores_ids,  
        "id_adulto": np.random.choice(adultos_ids, size=10),
        "nombre": ["Sofía", "Mateo", "Valentina", "Lucas", "Isabella", "Diego", "Camila", "Santiago", "Lucía", "Martina"]
    })

    # Tabla: zonas restringidas
    zonas_nombres = ["Parque Norte", "Zona Industrial", "Centro Urbano", "Área Restringida A", "Perímetro Seguridad"]

    # Historico_ubicaciones (Vulneraciones trimestrales)
    registros = []
    # Generamos datos repartidos en todo el año 2026
    fechas = pd.date_range(start="2025-02-22", end="2026-02-22", freq="D")
    
    for _ in range(600):
        fecha = np.random.choice(fechas)
        registros.append({
            "id": str(uuid.uuid4()),
            "id_menor": np.random.choice(menores_ids),
            "zona_vulnerada": np.random.choice(zonas_nombres),
            "fecha": fecha,
            "estado": "alarma",
            "duracion": np.random.randint(1, 60)
        })
    
    df_historial = pd.DataFrame(registros)
    # Merge para que la tabla y gráficos tengan el NOMBRE del niño
    df_final = df_historial.merge(df_menores[['id', 'nombre']], left_on='id_menor', right_on='id')
    return df_final, df_menores

# CARGAMOS LOS DATOS GLOBALES
df_master, df_menores_list = generate_bq_data()

# ==========================================================
# 2️⃣ ESTILO CORPORATIVO (ADMIN DARK MODE)
# ==========================================================
FONDO_COLOR = "#111723"  
TARJETA_COLOR = "#1E2633"  
TEXTO_COLOR = "#FFFFFF"
ACCENTO_COLOR = "#6684E8" 
PALETTE = ["#6684E8", "#EF7581", "#8EEDBF", "#FFD166", "#CD71FB"]

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(style={"backgroundColor": FONDO_COLOR, "minHeight": "100vh", "padding": "25px", "color": TEXTO_COLOR, "fontFamily": "Inter, sans-serif"}, children=[
    
    # Header Corporativo
    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "30px"}, children=[
        html.Div([
            html.H1("SafeChild Guardian AI", style={"margin": "0", "fontSize": "28px", "fontWeight": "bold", "color": ACCENTO_COLOR}),
            html.P("ADMINISTRATOR CONTROL PANEL • REAL-TIME MONITORING", style={"margin": "0", "opacity": "0.6", "fontSize": "12px", "letterSpacing": "2px"})
        ]),
        html.Div([
            html.Label("Filtro de Menores:", style={"fontSize": "12px", "marginBottom": "5px", "display": "block"}),
            dcc.Dropdown(
                id="selector-menor",
                options=[{"label": "Todos los Menores", "value": "ALL"}] + [{"label": n, "value": n} for n in sorted(df_master["nombre"].unique())],
                value="ALL",
                clearable=False,
                style={"width": "300px", "color": "#000"}
            )
        ])
    ]),

    # Fila de Gráficos Principales
    html.Div(style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}, children=[
        
        # Tarjeta 1: Tendencia (Líneas)
        html.Div(style={"flex": "2", "backgroundColor": TARJETA_COLOR, "padding": "20px", "borderRadius": "12px", "boxShadow": "0 10px 20px rgba(0,0,0,0.3)"}, children=[
            html.H5("Tendencia Trimestral de Vulneraciones", style={"fontSize": "16px", "marginBottom": "20px", "opacity": "0.8"}),
            dcc.Graph(id="grafico-tendencia", style={"height": "400px"})
        ]),

        # Tarjeta 2: Distribución por Zonas (Donut)
        html.Div(style={"flex": "1", "backgroundColor": TARJETA_COLOR, "padding": "20px", "borderRadius": "12px", "boxShadow": "0 10px 20px rgba(0,0,0,0.3)"}, children=[
            html.H5("% Impacto por Zona Restringida", style={"fontSize": "16px", "marginBottom": "20px", "opacity": "0.8"}),
            dcc.Graph(id="grafico-tarta", style={"height": "400px"})
        ])
    ]),

    # Tabla de Registro
    html.Div(style={"marginTop": "25px", "backgroundColor": TARJETA_COLOR, "padding": "20px", "borderRadius": "12px"}, children=[
        html.H5("Registro de Auditoría - Últimas Alertas detectadas", style={"fontSize": "16px", "marginBottom": "15px"}),
        dash_table.DataTable(
            id="tabla-admin",
            columns=[{"name": i.upper(), "id": i} for i in ["nombre", "zona_vulnerada", "fecha", "duracion"]],
            page_size=8,
            style_header={"backgroundColor": "#2A3444", "color": ACCENTO_COLOR, "fontWeight": "bold", "border": "none"},
            style_cell={"backgroundColor": TARJETA_COLOR, "color": TEXTO_COLOR, "textAlign": "left", "padding": "12px", "borderBottom": "1px solid #2A3444"},
            style_data={"border": "none"},
            sort_action="native"
        )
    ])
])

# ==========================================================
# 3️⃣ CALLBACK CORREGIDO
# ==========================================================
@app.callback(
    [Output("grafico-tendencia", "figure"),
     Output("grafico-tarta", "figure"),
     Output("tabla-admin", "data")],
    [Input("selector-menor", "value")]
)
def update_dashboard(selected_name): # CORREGIDO: Eliminada definición doble de función
    dff = df_master.copy()
    if selected_name != "ALL":
        dff = dff[dff["nombre"] == selected_name]

    dff['mes_año'] = dff['fecha'].dt.strftime('%b %Y')

    #nombres de los trimestres 
    trimestres_es = {1: "Enero - Marzo", 2: "Abril - Junio", 3: "Julio - Septiembre", 4: "Octubre - Diciembre"}
    
    # 2. Creamos identificadores cronológicos (Año + Trimestre)
    dff['trimestre_num'] = dff['fecha'].dt.quarter
    dff['año'] = dff['fecha'].dt.year
    dff['trimestre_label'] = dff['trimestre_num'].map(trimestres_es)
    
    # Creamos la etiqueta visible: "Enero - Marzo 2025"
    dff['periodo_trimestral'] = dff['trimestre_label'] + " " + dff['año'].astype(str)
    
    # Creamos una clave numérica para ordenar: 20251, 20252, 20261...
    dff['orden_cronologico'] = dff['año'] * 10 + dff['trimestre_num']

    # 3. Agrupamos por este nuevo periodo incluyendo el orden
    trend_data = dff.groupby(['periodo_trimestral', 'orden_cronologico', 'nombre']).size().reset_index(name='vulneraciones')
    
    # 4. Ordenamos por la clave cronológica para que el gráfico fluya correctamente en el tiempo
    trend_data = trend_data.sort_values('orden_cronologico')

    # Extraemos el orden exacto de las etiquetas para el eje X
    orden_etiquetas = trend_data['periodo_trimestral'].unique()

    fig_trend = px.line(
        trend_data, 
        x="periodo_trimestral", 
        y="vulneraciones", 
        color="nombre",
        markers=True, 
        template="plotly_dark", 
        color_discrete_sequence=PALETTE
    )

    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="<b>HISTÓRICO TRIMESTRAL (2025-2026)</b>", 
            title_font=dict(color=ACCENTO_COLOR),
            showgrid=False, 
            categoryorder='array', 
            categoryarray=orden_etiquetas # Forzamos el orden cronológico Feb 25 -> Feb 26
        ),
        yaxis=dict(
            title="<b>VULNERACIONES</b>", 
            title_font=dict(color=ACCENTO_COLOR),
            gridcolor="#2A3444"
        ),
        margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # 2. Gráfico de Tarta (Donut corporativo)
    zona_data = dff.groupby("zona_vulnerada").size().reset_index(name="conteo")
    fig_pie = px.pie(
        zona_data, names="zona_vulnerada", values="conteo",
        hole=0.6,
        color_discrete_sequence=PALETTE,
        template="plotly_dark"
    )
    fig_pie.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')

    # 3. Datos para la tabla (Convertir fechas a string)
    df_tabla = dff.sort_values("fecha", ascending=False)
    df_tabla['fecha'] = df_tabla['fecha'].dt.strftime('%Y-%m-%d')
    tabla_data = df_tabla.to_dict("records")

    return fig_trend, fig_pie, tabla_data


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run_server(host="0.0.0.0", port=port, debug=False)