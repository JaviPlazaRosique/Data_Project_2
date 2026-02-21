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
        # Nota: He incluido los campos de contacto y dirección para la ficha dinámica
        query = """
            SELECT id_menor, count(*) as alertas, 
            ANY_VALUE(latitud) as lat, ANY_VALUE(longitud) as lon, 
            ANY_VALUE(tipo_alerta) as tipo_alerta,
            ANY_VALUE(direccion_aproximada) as direccion,
            ANY_VALUE(nombre_padre) as padre,
            ANY_VALUE(telefono_padre) as contacto
            FROM `gemma-12.monitoreo_dataset.alertas` 
            GROUP BY id_menor 
            ORDER BY alertas DESC
        """
        df = client.query(query).to_dataframe()
        if df.empty: raise ValueError("Tabla vacía")
        return df
    except Exception as e:
        print(f"DEBUG: Error al conectar a BigQuery: {e}")
        # Datos de respaldo (Javi incluido para pruebas)
        return pd.DataFrame({
            "id_menor": ["Javi", "Marta", "Luis", "M-04"],
            "lat": [40.4167, 40.4200, 40.4150, 40.4180],
            "lon": [-3.7037, -3.7100, -3.7000, -3.7050],
            "tipo_alerta": ["Zona Restringida", "Zona Restringida", "Zona Restringida", "Acercamiento"],
            "alertas": [10, 8, 5, 2],
            "direccion": ["Calle Mayor 1, Madrid", "Av. Complutense 23", "Paseo del Prado 5", "Calle Atocha s/n"],
            "padre": ["Pedro García", "Ana López", "Roberto Sanz", "Lucía Ruiz"],
            "contacto": ["600 000 001", "600 000 002", "600 000 003", "600 000 004"]
        })

df_global = get_data()

# --- Componente Reutilizable: Tarjeta de Negocio ---
def business_logic_card(titulo, texto):
    return html.Div(
        style={
            "backgroundColor": AZUL_CLARO, "padding": "20px", "borderRadius": "8px",
            "marginBottom": "25px", "borderLeft": f"7px solid {AZUL_OSCURO}"
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
                html.Span(" 🛡️", style={"fontSize": "35px"})
            ]
        ),

        dcc.Tabs(id="tabs-sistema", value='tab-1', children=[
            
            # PESTAÑA 1: CONTEXTO
            dcc.Tab(label="📘 Contexto", value="tab-1", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Visión General del Sistema", style={"color": AZUL_OSCURO, "fontSize": "28px"}),
                    business_logic_card("📑 Índice de Visualizaciones", 
                        "1. **Reincidencia**\n2. **Mapa General**\n3. **Estado del Servicio**\n4. **Intervención por Permanencia**"),
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
                    html.H2("Monitor de Conectividad", style={"color": AZUL_OSCURO}),
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

            # PESTAÑA 5: PERMANENCIA CRÍTICA (ACTUALIZADA CON FICHA)
            dcc.Tab(label="⏳ Permanencia Crítica", value="tab-permanencia", children=[
                html.Div(style={"backgroundColor": "#ffffff", "padding": "40px", "borderRadius": "0 0 15px 15px"}, children=[
                    html.H2("Intervención en Zonas Prolongadas (> 5 mins)", style={"color": AZUL_OSCURO}),
                    
                    html.Label("🔍 Seleccionar Menor para Intervención:", style={"fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="dropdown-niño-perm",
                        options=[{"label": i, "value": i} for i in df_global["id_menor"].unique()],
                        placeholder="Escriba el nombre del niño...",
                        style={"marginBottom": "20px"}
                    ),

                    html.Div(style={"display": "flex", "gap": "20px"}, children=[
                        # LADO IZQUIERDO: MAPA
                        html.Div(style={"flex": "2"}, children=[
                            dcc.Graph(id="mapa-permanencia")
                        ]),
                        
                        # LADO DERECHO: FICHA DE DATOS
                        html.Div(id="ficha-niño", style={
                            "flex": "1", "padding": "25px", "borderRadius": "15px", 
                            "border": f"2px solid {AZUL_OSCURO}", "backgroundColor": "#f8f9fa",
                            "boxShadow": "0 4px 8px rgba(0,0,0,0.05)"
                        })
                    ])
                ])
            ])
        ])
    ]
)

# --- CALLBACKS ---

@app.callback(Output("mapa-alertas", "figure"), Input("tabs-sistema", "value"))
def render_map(tab):
    if tab != 'tab-3': return dash.no_update
    fig = px.scatter_mapbox(df_global, lat="lat", lon="lon", color="tipo_alerta", size="alertas",
                            color_discrete_map={"Acercamiento": "#FFD700", "Zona Restringida": "#FF0000"}, zoom=12, height=600)
    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
    return fig

@app.callback(Output("grafico-barras-alertas", "figure"), Input("pestaña-niño", "value"))
def actualizar_grafico(seleccion):
    df_plot = df_global.head(10) if (not seleccion or "ALL" in seleccion) else df_global[df_global["id_menor"].isin(seleccion if isinstance(seleccion, list) else [seleccion])]
    fig = px.bar(df_plot, x="id_menor", y="alertas", text="alertas", color_discrete_sequence=[AZUL_OSCURO])
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

# Callback Dinámico para Mapa 📍 y Ficha de Padres
@app.callback(
    [Output("mapa-permanencia", "figure"),
     Output("ficha-niño", "children")],
    [Input("dropdown-niño-perm", "value"),
     Input("tabs-sistema", "value")]
)
def update_permanencia(niño_seleccionado, tab):
    if tab != 'tab-permanencia': return dash.no_update, dash.no_update
    
    # Filtrar solo zonas restringidas
    df_restr = df_global[df_global["tipo_alerta"] == "Zona Restringida"]
    
    if niño_seleccionado:
        df_display = df_restr[df_restr["id_menor"] == niño_seleccionado]
        zoom_val = 15
    else:
        df_display = df_restr
        zoom_val = 12

    # 1. Mapa 📍
    fig = px.scatter_mapbox(df_display, lat="lat", lon="lon", zoom=zoom_val, height=600)
    fig.update_traces(
        marker=dict(size=15, color=ROJO_ALERTA),
        mode='markers+text',
        text=["📍" for _ in range(len(df_display))],
        textposition="top center"
    )
    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)

    # 2. Ficha de Datos
    if niño_seleccionado and not df_display.empty:
        info = df_display.iloc[0]
        ficha = [
            html.H2(f"👤 {info['id_menor']}", style={"color": AZUL_OSCURO, "marginTop": "0"}),
            html.Hr(),
            html.P([html.B("📍 Dirección Aproximada: "), html.Br(), info['direccion']], style={"fontSize": "16px"}),
            html.P([html.B("🚨 Alertas de Permanencia: "), info['alertas']], style={"fontSize": "16px"}),
            html.Div(style={"marginTop": "30px", "padding": "20px", "backgroundColor": "#ffebee", "borderRadius": "12px", "border": f"1px solid {ROJO_ALERTA}"}, children=[
                html.B("📞 CONTACTO DE EMERGENCIA:", style={"color": ROJO_ALERTA}),
                html.P(f"Padre/Madre: {info['padre']}", style={"margin": "10px 0 5px 0"}),
                html.P(f"Teléfono: {info['contacto']}", style={"fontWeight": "bold", "fontSize": "18px"})
            ])
        ]
    else:
        ficha = html.P("Seleccione un menor en el buscador superior para ver su ubicación exacta y datos de contacto de los padres.", 
                       style={"color": GRIS_TEXTO, "textAlign": "center", "marginTop": "50%"})

    return fig, ficha

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)