import dash
from dash import html, dcc, Input, Output
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
import os

# --- Configuración de Estilos ---
AZUL_OSCURO = "#002b5c"  
GRIS_TEXTO = "#546e7a" 

app = dash.Dash(__name__)
server = app.server

# --- Función de Datos con Protección ---
def get_data():
    try:
        client = bigquery.Client()
        # Nota: Asegúrate de que tu tabla tenga lat, lon y tipo_alerta para el mapa
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
        # Datos de respaldo para que la app no se rompa
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
            "backgroundColor": "#e3f2fd", 
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

        # Sistema de Pestañas Corregido
        dcc.Tabs(id="tabs-sistema", value='tab-1', children=[
            
            # PESTAÑA 1: CONTEXTO
            dcc.Tab(label="📘 Contexto", value="tab-1", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Visión General del Sistema", style={"color": AZUL_OSCURO, "fontSize": "28px"}),
                    html.P("Panel de supervisión que centraliza métricas clave sobre alertas geolocalizadas.", style={"fontSize": "20px", "color": GRIS_TEXTO}),
                    
                    business_logic_card("📑 Índice de Visualizaciones", 
                        "1. **Reincidencia**\n2. **Zonas Activas**\n3. **Monitor Real-Time**\n4. **Permanencia**\n5. **Concentración**\n6. **Respuesta Parental**"),
                    
                    html.Hr(style={"margin": "40px 0"}),
                    html.Div(style={"display": "flex", "justifyContent": "center", "gap": "40px"}, children=[
                        html.Img(src="https://th.bing.com/th/id/OIP.uz6u9Xls7SQHPJJghTDm8gHaFj?w=247", style={"width": "280px", "borderRadius": "12px"}),
                        html.Img(src="https://th.bing.com/th/id/OIP.2VPX9qwHuszZUJk2yPry6gHaEK?w=289", style={"width": "280px", "borderRadius": "12px"})
                    ])
                ])
            ]),

            # PESTAÑA 2: DASHBOARD (GRÁFICO DE BARRAS)
            dcc.Tab(label="📊 Ranking reincidencia", value="tab-2", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "30px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Ranking de Reincidencia Crítica", style={"color": AZUL_OSCURO}),
                    business_logic_card("📊 Análisis de Alertas", "Filtre por ID de menor para analizar el riesgo individual."),
                    
                    html.Label("Seleccionar niños específicos:", style={"fontWeight": "600", "fontSize": "18px"}),
                    dcc.Dropdown(
                        id="pestaña-niño",
                        options=[{"label": "Ver Todos (Top 10)", "value": "ALL"}] + 
                                [{"label": f"ID Menor: {i}", "value": i} for i in df_global["id_menor"].unique()],
                        value="ALL", multi=True, clearable=False, style={"marginTop": "10px", "marginBottom": "20px"}
                    ),
                    dcc.Graph(id="grafico-barras-alertas")
                ])
            ]),

            # PESTAÑA 3: MAPA DE RIESGO
            dcc.Tab(label="📍 Mapa de Riesgo", value="tab-3", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Concentración Geográfica", style={"color": AZUL_OSCURO, "fontSize": "28px"}),
                    business_logic_card("📌 Lógica de Mapa", "🟡 **Amarillo**: Proximidad | 🔴 **Rojo**: Incursión"),
                    dcc.Graph(id="mapa-alertas")
                ])
            ]),

            # PESTAÑA 4: INSIGHTS
            dcc.Tab(label="🚨 Insights", value="tab-4", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Conclusiones Clave", style={"color": AZUL_OSCURO}),
                    business_logic_card("🔎 Interpretación", "Evaluación comparativa para intervenciones preventivas.")
                ])
            ])
        ])
    ]
)

# --- CALLBACKS ---

# Callback para el Mapa
@app.callback(
    Output("mapa-alertas", "figure"),
    Input("tabs-sistema", "value")
)
def render_map(tab):
    if tab != 'tab-3': return dash.no_update
    color_map = {"Acercamiento": "#FFD700", "Zona Restringida": "#FF0000"}
    fig = px.scatter_mapbox(df_global, lat="lat", lon="lon", color="tipo_alerta", size="alertas",
                            color_discrete_map=color_map, zoom=12, height=600)
    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
    return fig

# Callback para el Gráfico de Barras
@app.callback(
    Output("grafico-barras-alertas", "figure"),
    Input("pestaña-niño", "value")
)
def actualizar_grafico(seleccion):
    if not seleccion or "ALL" in seleccion:
        df_plot = df_global.head(10)
    else:
        lista_seleccion = seleccion if isinstance(seleccion, list) else [seleccion]
        df_plot = df_global[df_global["id_menor"].isin(lista_seleccion)]

    fig = px.bar(df_plot, x="id_menor", y="alertas", text="alertas", color_discrete_sequence=[AZUL_OSCURO])
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=AZUL_OSCURO))
    return fig

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)