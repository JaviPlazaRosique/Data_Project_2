import dash
from dash import html, dcc, Input, Output
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
import os

# --- Configuración de Estilos ---
AZUL_OSCURO = "#002b5c"  
GRIS_TEXTO = "#546e7a" 
ROJO_ALERTA = "#d32f2f" 
AZUL_CLARO = "#e3f2fd"

app = dash.Dash(__name__)
server = app.server

# --- Función de Datos con Protección ---
def get_data():
    try:
        client = bigquery.Client()
        query = """
            SELECT id_menor, count(*) as alertas, 
            ANY_VALUE(latitud) as lat, ANY_VALUE(longitud) as lon, ANY_VALUE(tipo_alerta) as tipo_alerta
            FROM `gemma-12.monitoreo_dataset.alertas` 
            GROUP BY id_menor 
            ORDER BY alertas DESC
        """
        df = client.query(query).to_dataframe()
        if df.empty:
            raise ValueError("Tabla vacía")
        return df
    except Exception as e:
        print(f"DEBUG: Error al conectar a BigQuery: {e}")
        # Datos de respaldo para pruebas
        return pd.DataFrame({
            "id_menor": ["M-01", "M-02", "M-03", "M-04"],
            "lat": [40.4167, 40.4200, 40.4150, 40.4180],
            "lon": [-3.7037, -3.7100, -3.7000, -3.7050],
            "tipo_alerta": ["Acercamiento", "Zona Restringida", "Acercamiento", "Zona Restringida"],
            "alertas": [10, 8, 5, 2]
        })

df_global = get_data()

# --- Componente Reutilizable: Tarjeta de Negocio ---
def business_logic_card(titulo, texto):
    return html.Div(
        style={
            "backgroundColor": AZUL_CLARO, 
            "padding": "20px",
            "borderRadius": "8px",
            "marginBottom": "25px",
            "borderLeft": f"7px solid {AZUL_OSCURO}"
        },
        children=[
            html.B(titulo, style={"color": AZUL_OSCURO, "display": "block", "marginBottom": "10px", "fontSize": "18px"}),
            dcc.Markdown(texto, style={"color": GRIS_TEXTO, "fontSize": "16px", "lineHeight": "1.5", "margin": "0"})
        ]
    )

# --- Layout Principal ---
app.layout = html.Div(
    style={"backgroundColor": "#f4f6fb", "minHeight": "100vh", "padding": "20px", "fontFamily": "Segoe UI, Arial"},
    children=[
        # Cabecera Única
        html.Div(
            style={"backgroundColor": "#ffffff", "padding": "25px", "borderRadius": "15px", "textAlign": "center", "marginBottom": "25px", "borderBottom": f"4px solid {AZUL_OSCURO}"},
            children=[
                html.H1("SafeChild Guardian AI - Panel de Alertas", style={"color": AZUL_OSCURO, "fontWeight": "bold", "display": "inline"}),
                html.Span(" 📍", style={"fontSize": "35px"})
            ]
        ),

        # Sistema de Pestañas
        dcc.Tabs(id="tabs-sistema", value='tab-1', children=[
            
            # PESTAÑA 1: CONTEXTO
            dcc.Tab(label="📘 Contexto", value="tab-1", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Visión General del Sistema", style={"color": AZUL_OSCURO, "fontSize": "28px"}),
                    business_logic_card("📑 Índice de Visualizaciones", 
                        "1. **Reincidencia**\n2. **Mapa de Riesgo General**\n3. **Estado del Servicio**\n4. **Permanencia Crítica (> 5 min)**"),
                    
                    html.Hr(style={"margin": "40px 0"}),
                    html.Div(style={"display": "flex", "justifyContent": "center", "gap": "40px"}, children=[
                        html.Img(src="https://th.bing.com/th/id/OIP.uz6u9Xls7SQHPJJghTDm8gHaFj?w=247", style={"width": "280px", "borderRadius": "12px"}),
                        html.Img(src="https://th.bing.com/th/id/OIP.2VPX9qwHuszZUJk2yPry6gHaEK?w=289", style={"width": "280px", "borderRadius": "12px"})
                    ])
                ])
            ]),

            # PESTAÑA 2: RANKING REINCIDENCIA
            dcc.Tab(label="📊 Ranking reincidencia", value="tab-2", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "30px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Ranking de Reincidencia Crítica", style={"color": AZUL_OSCURO}),
                    dcc.Dropdown(
                        id="pestaña-niño",
                        options=[{"label": "Ver Todos (Top 10)", "value": "ALL"}] + 
                                [{"label": f"ID Menor: {i}", "value": i} for i in df_global["id_menor"].unique()],
                        value="ALL", multi=True, clearable=False, style={"marginBottom": "20px"}
                    ),
                    dcc.Graph(id="grafico-barras-alertas")
                ])
            ]),

            # PESTAÑA 3: MAPA DE RIESGO GENERAL
            dcc.Tab(label="📍 Mapa de Riesgo", value="tab-3", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Concentración Geográfica de Alertas", style={"color": AZUL_OSCURO}),
                    dcc.Graph(id="mapa-alertas")
                ])
            ]),

            # PESTAÑA 4: ESTADO DEL SERVICIO
            dcc.Tab(label="📈 Estado del Servicio", value="tab-5", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Monitor de Conectividad y Alertas Activas", style={"color": AZUL_OSCURO}),
                    html.Div(style={"display": "flex", "justifyContent": "space-around", "marginTop": "20px"}, children=[
                        html.Div(style={"textAlign": "center", "padding": "20px", "border": f"2px solid {AZUL_OSCURO}", "borderRadius": "15px", "width": "40%"}, children=[
                            html.H3("Niños Conectados"),
                            html.H1(len(df_global["id_menor"].unique()), style={"fontSize": "60px"})
                        ]),
                        html.Div(style={"textAlign": "center", "padding": "20px", "border": f"2px solid {ROJO_ALERTA}", "borderRadius": "15px", "width": "40%"}, children=[
                            html.H3("Alarmas Activas"),
                            html.H1(df_global["alertas"].sum(), style={"color": ROJO_ALERTA, "fontSize": "60px"})
                        ])
                    ])
                ])
            ]),

            # PESTAÑA 5: PERMANENCIA CRÍTICA (> 5 MIN)
            dcc.Tab(label="⏳ Permanencia Crítica", value="tab-permanencia", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Zonas de Permanencia Prolongada (> 5 mins)", style={"color": AZUL_OSCURO}),
                    business_logic_card("🕒 Detección de Riesgo Estático", 
                        "Marcadores 📍 indican ubicaciones donde los menores permanecen en zonas restringidas por tiempo excesivo."),
                    dcc.Graph(id="mapa-permanencia")
                ])
            ])
        ])
    ]
)

# --- CALLBACKS ---

# Callback para el Mapa de Riesgo General
@app.callback(Output("mapa-alertas", "figure"), Input("tabs-sistema", "value"))
def render_map(tab):
    if tab != 'tab-3': return dash.no_update
    fig = px.scatter_mapbox(df_global, lat="lat", lon="lon", color="tipo_alerta", size="alertas",
                            color_discrete_map={"Acercamiento": "#FFD700", "Zona Restringida": "#FF0000"}, zoom=12, height=600)
    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
    return fig

# Callback para el Gráfico de Barras
@app.callback(Output("grafico-barras-alertas", "figure"), Input("pestaña-niño", "value"))
def actualizar_grafico(seleccion):
    df_plot = df_global.head(10) if (not seleccion or "ALL" in seleccion) else df_global[df_global["id_menor"].isin(seleccion if isinstance(seleccion, list) else [seleccion])]
    fig = px.bar(df_plot, x="id_menor", y="alertas", text="alertas", color_discrete_sequence=[AZUL_OSCURO])
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

# Callback para el Mapa de Permanencia con Emoji 📍
@app.callback(Output("mapa-permanencia", "figure"), Input("tabs-sistema", "value"))
def render_mapa_permanencia(tab):
    if tab != 'tab-permanencia': return dash.no_update
    df_perm = df_global[df_global["tipo_alerta"] == "Zona Restringida"].copy()
    
    fig = px.scatter_mapbox(df_perm, lat="lat", lon="lon", zoom=13, height=600)
    
    fig.update_traces(
        marker=dict(size=12, color=ROJO_ALERTA),
        mode='markers+text',
        text=["📍" for _ in range(len(df_perm))],
        textposition="top center"
    )
    
    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
    return fig

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)