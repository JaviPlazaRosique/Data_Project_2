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
AMARILLO_INFO = "#FFA000"
VERDE_OK = "#388E3C"

app = dash.Dash(__name__)
server = app.server

# --- Datos de prueba / BigQuery ---
def get_data():
    try:
        client = bigquery.Client()
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
    except:
        return pd.DataFrame({
            "id_menor": ["Javi","Marta","Luis","M-04"],
            "lat": [40.4167,40.4200,40.4150,40.4180],
            "lon": [-3.7037,-3.7100,-3.7000,-3.7050],
            "tipo_alerta": ["Zona Restringida","Zona Restringida","Zona Restringida","Acercamiento"],
            "alertas": [10,8,5,2],
            "direccion": ["Calle Mayor 1","Av. Complutense 23","Paseo del Prado 5","Calle Atocha s/n"],
            "padre": ["Pedro García","Ana López","Roberto Sanz","Lucía Ruiz"],
            "contacto": ["600 000 001","600 000 002","600 000 003","600 000 004"]
        })

df_global = get_data()

# --- Componente Tarjeta Reutilizable ---
def kpi_card(titulo, valor, color=AZUL_OSCURO, subtexto=None):
    return html.Div(style={"backgroundColor": AZUL_CLARO,"padding":"20px","borderRadius":"15px",
                           "textAlign":"center","width":"200px","borderLeft":f"7px solid {color}"},
                    children=[
                        html.H4(titulo, style={"color":color,"marginBottom":"5px"}),
                        html.H2(valor, style={"color":color,"margin":"0"}),
                        html.P(subtexto or "", style={"color":GRIS_TEXTO,"fontSize":"12px"})
                    ])

# --- Layout Principal ---
app.layout = html.Div(style={"backgroundColor":"#f4f6fb","minHeight":"100vh","padding":"20px","fontFamily":"Segoe UI, Arial"},
                      children=[
    html.Div(style={"backgroundColor":"#ffffff","padding":"25px","borderRadius":"15px",
                    "textAlign":"center","marginBottom":"25px","borderBottom":f"4px solid {AZUL_OSCURO}"},
             children=[html.H1("SafeChild Guardian AI", style={"color":AZUL_OSCURO,"fontWeight":"bold"}),
                       html.Span(" 🛡️", style={"fontSize":"35px"})]),

    dcc.Tabs(id="tabs-sistema", value='tab-1', children=[

        # --- CONTEXTO ---
        dcc.Tab(label="📘 Contexto", value="tab-1", children=[
            html.Div(style={"backgroundColor":"#ffffff","padding":"40px","borderRadius":"0 0 15px 15px"},
                     children=[
                         html.H2("Visión General del Sistema", style={"color":AZUL_OSCURO,"fontSize":"28px"}),
                         html.P("Este panel permite monitorizar alertas, reincidencias y permanencia en zonas críticas.",
                                style={"color":GRIS_TEXTO,"fontSize":"16px"}),
                         html.Div(style={"display":"flex","gap":"20px","marginTop":"20px"}, children=[
                             kpi_card("Total Niños", len(df_global["id_menor"].unique())),
                             kpi_card("Total Alertas", df_global["alertas"].sum(), ROJO_ALERTA),
                             kpi_card("Zonas Críticas", len(df_global[df_global["alertas"]>5]), AMARILLO_INFO)
                         ])
                     ])
        ]),

        # --- RANKING REINCIDENCIA ---
        dcc.Tab(label="📊 Ranking Reincidencia", value="tab-2", children=[
            html.Div(style={"backgroundColor":"#ffffff","padding":"30px","borderRadius":"0 0 15px 15px"}, children=[
                html.H2("Ranking de Reincidencia Crítica", style={"color":AZUL_OSCURO}),
                html.P("Seleccione uno o varios menores para ver su nivel de reincidencia y distribución acumulativa."),
                dcc.Dropdown(id="pestaña-niño", options=[{"label":"Ver Todos (Top 10)","value":"ALL"}]+
                             [{"label":f"ID Menor: {i}","value":i} for i in df_global["id_menor"].unique() if i!="M-04"],
                             value="ALL", multi=True, clearable=False, style={"marginBottom":"20px"}),
                html.Div(style={"display":"flex","gap":"40px"}, children=[
                    dcc.Graph(id="grafico-barras-alertas", style={"flex":"2"}),
                    dcc.Graph(id="grafico-pareto-alertas", style={"flex":"1"})
                ])
            ])
        ]),

        # --- MAPA DE RIESGO ---
        dcc.Tab(label="📍 Mapa de Riesgo", value="tab-3", children=[
            html.Div(style={"backgroundColor":"#ffffff","padding":"40px","borderRadius":"0 0 15px 15px"}, children=[
                html.H2("Mapa de Concentración de Alertas", style={"color":AZUL_OSCURO}),
                html.P("Visualiza la ubicación de las alertas y la densidad por zona."),
                html.Div(style={"display":"flex","gap":"20px"}, children=[
                    dcc.Graph(id="mapa-alertas", style={"flex":"2"}),
                    dcc.Graph(id="heatmap-alertas", style={"flex":"1"})
                ])
            ])
        ]),

        # --- ESTADO DEL SERVICIO ---
        dcc.Tab(label="📈 Estado del Servicio", value="tab-5", children=[
            html.Div(style={"backgroundColor":"#ffffff","padding":"40px","borderRadius":"0 0 15px 15px"}, children=[
                html.H2("Monitor de Conectividad y Alertas", style={"color":AZUL_OSCURO}),
                html.P("Resumen de KPIs y distribución de tipos de alerta."),
                html.Div(style={"display":"flex","gap":"20px","marginTop":"20px"}, children=[
                    kpi_card("Niños Conectados", len(df_global[df_global["id_menor"]!="M-04"]["id_menor"])),
                    kpi_card("Alarmas Activas", df_global[df_global["id_menor"]!="M-04"]["alertas"].sum(), ROJO_ALERTA),
                    kpi_card("Zonas Críticas", len(df_global[(df_global["alertas"]>5) & (df_global["id_menor"]!="M-04")]), AMARILLO_INFO)
                ]),
                html.Div(style={"display":"flex","gap":"20px","marginTop":"20px"}, children=[
                    dcc.Graph(id="grafico-torta-alertas", style={"flex":"1"}),
                    dcc.Graph(id="grafico-barra-alertas-tipo", style={"flex":"1"})
                ])
            ])
        ]),

        # --- PERMANENCIA CRÍTICA ---
        dcc.Tab(label="⏳ Permanencia Crítica", value="tab-permanencia", children=[
            html.Div(style={"backgroundColor":"#ffffff","padding":"40px","borderRadius":"0 0 15px 15px"}, children=[
                html.H2("Intervención en Zonas Prolongadas (> 5 mins)", style={"color":AZUL_OSCURO}),
                html.P("Seleccione un menor para ver su ubicación exacta y ficha de contacto de padres."),
                dcc.Dropdown(id="dropdown-niño-perm",
                             options=[{"label":i,"value":i} for i in df_global["id_menor"].unique() if i!="M-04"],
                             placeholder="Escriba el nombre del niño...", style={"marginBottom":"20px"}),
                html.Div(style={"display":"flex","gap":"20px"}, children=[
                    dcc.Graph(id="mapa-permanencia", style={"flex":"2"}),
                    html.Div(id="ficha-niño", style={"flex":"1","padding":"25px","borderRadius":"15px",
                                                     "border":f"2px solid {AZUL_OSCURO}","backgroundColor":"#f8f9fa",
                                                     "boxShadow":"0 4px 8px rgba(0,0,0,0.05)"})
                ]),
                dcc.Graph(id="grafico-barra-permanencia", style={"marginTop":"30px"})
            ])
        ])
    ])
])

# --- CALLBACKS básicos de gráficos ---
@app.callback(Output("grafico-barras-alertas","figure"), Input("pestaña-niño","value"))
def grafico_barras(seleccion):
    df_plot = df_global[df_global["id_menor"]!="M-04"]
    if not seleccion or "ALL" in seleccion:
        df_plot = df_plot.head(10)
    else:
        df_plot = df_plot[df_plot["id_menor"].isin(seleccion if isinstance(seleccion,list) else [seleccion])]
    fig = px.bar(df_plot.sort_values("alertas", ascending=True), x="alertas", y="id_menor", orientation="h",
                 text="alertas", color="alertas", color_continuous_scale="Blues", height=500)
    fig.update_traces(textposition="outside")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

@app.callback(Output("grafico-pareto-alertas","figure"), Input("pestaña-niño","value"))
def grafico_pareto(seleccion):
    df_plot = df_global[df_global["id_menor"]!="M-04"]
    if not seleccion or "ALL" in seleccion:
        df_plot = df_plot.head(10)
    else:
        df_plot = df_plot[df_plot["id_menor"].isin(seleccion if isinstance(seleccion,list) else [seleccion])]
    df_plot = df_plot.sort_values("alertas", ascending=False)
    df_plot["acum_perc"] = df_plot["alertas"].cumsum()/df_plot["alertas"].sum()*100
    fig = px.line(df_plot, x="id_menor", y="acum_perc", markers=True, height=400)
    fig.update_layout(yaxis_title="Acumulado (%)", xaxis_title="Menor")
    return fig


if __name__=="__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT",8080)), debug=False)