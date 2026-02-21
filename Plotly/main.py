import dash
from dash import html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import numpy as np
import os
from math import radians, cos, sin, sqrt, atan2

# ==========================================================
# 1️⃣ CONFIGURACIÓN Y GENERACIÓN DE DATOS
# ==========================================================
app = dash.Dash(__name__)
server = app.server

def distancia(lat1, lon1, lat2, lon2):
    R = 6371000 
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def generar_datos_fake():
    np.random.seed(42)
    adultos = pd.DataFrame({"id": [f"A-{i}" for i in range(1,6)], "nombre": ["Carlos","Ana","Laura","David","María"]})
    menores = pd.DataFrame({
        "id": [f"M-{i}" for i in range(1,11)],
        "id_adulto": np.random.choice(adultos["id"], 10),
        "nombre": ["Lucas","Mateo","Sofía","Valeria","Daniel","Paula","Mario","Elena","Diego","Laura"],
        "apellidos": ["García","Fernández","Martínez","Sánchez","Romero","Jiménez","Torres","Pérez","López","Ruiz"]
    })
    zonas_ref = [
        {"nombre": "Parque Central", "lat": 40.4167, "lon": -3.7037},
        {"nombre": "Zona Industrial", "lat": 40.4500, "lon": -3.6800},
        {"nombre": "Centro Comercial", "lat": 40.3900, "lon": -3.7200}
    ]
    registros = []
    for _ in range(500):
        menor = menores.sample(1).iloc[0]
        zona = np.random.choice(zonas_ref)
        u_lat, u_lon = zona["lat"] + np.random.uniform(-0.005, 0.005), zona["lon"] + np.random.uniform(-0.005, 0.005)
        d = distancia(zona["lat"], zona["lon"], u_lat, u_lon)
        fecha = pd.Timestamp("2026-01-01") + pd.to_timedelta(np.random.randint(0, 365), unit='D')
        
        registros.append({
            "nombre": menor["nombre"],
            "nombre_completo": f"{menor['nombre']} {menor['apellidos']}",
            "adulto": adultos[adultos["id"]==menor["id_adulto"]]["nombre"].values[0],
            "zona_nombre": zona["nombre"],
            "distancia": d,
            "fecha": fecha,
            "duracion_mins": np.random.randint(1, 45),
            "dia_nombre": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][fecha.dayofweek],
            "estado": "alarma" if d < 300 else "advertencia"
        })
    return pd.DataFrame(registros), adultos, menores

df_historial, adultos_df, menores_df = generar_datos_fake()

# ==========================================================
# 2️⃣ LAYOUT UNIFICADO
# ==========================================================
AZUL = "#0A1F44"
GRIS = "#F4F6FA"
ROJO = "#E74C3C"
NARANJA = "#F39C12"

app.layout = html.Div(style={"backgroundColor": GRIS, "padding": "20px", "fontFamily": "Segoe UI"}, children=[

    # Header
    html.Div(style={"backgroundColor": AZUL, "padding": "20px", "borderRadius": "8px", "color": "white", "marginBottom": "20px"}, children=[
        html.H2("📊 SafeChild Guardian AI - Panel de Control", style={"margin": "0"}),
    ]),

    # 1. KPIs
    html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "25px"}, children=[
        html.Div(style={"backgroundColor": "white", "padding": "15px", "borderRadius": "10px", "flex": "1", "textAlign": "center"}, children=[
            html.H6("Niños Activos"), html.H2(len(menores_df))
        ]),
        html.Div(style={"backgroundColor": "white", "padding": "15px", "borderRadius": "10px", "flex": "1", "textAlign": "center"}, children=[
            html.H6("Adultos"), html.H2(len(adultos_df))
        ]),
        html.Div(style={"backgroundColor": "#FDEDEC", "padding": "15px", "borderRadius": "10px", "flex": "1", "textAlign": "center"}, children=[
            html.H6("Alarmas", style={"color": ROJO}), html.H2(len(df_historial[df_historial["estado"]=="alarma"]), style={"color": ROJO})
        ]),
        html.Div(style={"backgroundColor": "#FEF9E7", "padding": "15px", "borderRadius": "10px", "flex": "1", "textAlign": "center"}, children=[
            html.H6("Advertencias", style={"color": NARANJA}), html.H2(len(df_historial[df_historial["estado"]=="advertencia"]), style={"color": NARANJA})
        ]),
    ]),

    # 2. Análisis de Reincidencia
    html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "8px", "marginBottom": "20px"}, children=[
        html.H4("Análisis de Reincidencia (Top 5)", style={"color": AZUL}),
        dcc.Dropdown(id="dropdown-menor", value="ALL", clearable=False, style={"width": "350px", "marginBottom": "10px"}),
        html.Div(id="panel-info", style={"marginBottom": "15px"}),
        html.Div(style={"display": "flex", "gap": "20px"}, children=[
            dcc.Graph(id="grafico-linea", style={"flex": "1"}),
            dcc.Graph(id="grafico-tarta", style={"flex": "1"})
        ])
    ]),

    # 3. Zonas y Permanencia
    html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "20px"}, children=[
        html.Div(style={"flex": "1", "backgroundColor": "white", "padding": "20px", "borderRadius": "8px"}, children=[
            html.H5("Día de mayor frecuencia por Zona", style={"color": AZUL}),
            dash_table.DataTable(
                id="tabla-zonas-dias",
                columns=[{"name": "Zona", "id": "zona_nombre"}, {"name": "Día Top", "id": "dia_nombre"}, {"name": "Visitas", "id": "visitas"}],
                style_header={"backgroundColor": AZUL, "color": "white"}
            )
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "white", "padding": "20px", "borderRadius": "8px"}, children=[
            html.H5("Permanencia Crítica (> 5 mins)", style={"color": AZUL}),
            dcc.Graph(id="grafico-permanencia")
        ])
    ]),

    # 4. Tabla de Incidentes
    html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "8px"}, children=[
        html.H4("Registro Detallado de Alarmas", style={"color": AZUL}),
        html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "15px"}, children=[
            dcc.Dropdown(id="filtro-tabla-menor", options=[{"label": "Todos", "value": "ALL"}] + [{"label": n, "value": n} for n in sorted(df_historial["nombre"].unique())], value="ALL", style={"width": "200px"}),
            dcc.Dropdown(id="filtro-tabla-estado", options=[{"label": "Alarma", "value": "alarma"}, {"label": "Advertencia", "value": "advertencia"}, {"label": "Todos", "value": "ALL"}], value="ALL", style={"width": "200px"}),
        ]),
        dash_table.DataTable(
            id="tabla-alertas",
            columns=[{"name": i.capitalize(), "id": i} for i in ["nombre", "adulto", "fecha", "estado", "duracion_mins"]],
            page_size=5,
            style_header={"backgroundColor": AZUL, "color": "white"},
            style_data_conditional=[
                {"if": {"filter_query": "{estado} eq 'alarma'"}, "color": ROJO, "fontWeight": "bold"},
                {"if": {"filter_query": "{estado} eq 'advertencia'"}, "color": NARANJA, "fontWeight": "bold"}
            ]
        )
    ])
])

# ==========================================================
# 3️⃣ CALLBACKS
# ==========================================================

@app.callback(
    [Output("dropdown-menor", "options"),
     Output("grafico-linea", "figure"),
     Output("grafico-tarta", "figure"),
     Output("panel-info", "children"),
     Output("tabla-zonas-dias", "data"),
     Output("grafico-permanencia", "figure")],
    [Input("dropdown-menor", "value")]
)
def actualizar_dashboard(selected):
    df_v = df_historial[df_historial["distancia"] <= 350].copy()
    top5_menores = df_v.groupby("nombre_completo").size().nlargest(5).index.tolist()
    opciones = [{"label": "Todos (Top 5)", "value": "ALL"}] + [{"label": n, "value": n} for n in top5_menores]

    # Gráficos
    df_plot = df_v[df_v["nombre_completo"].isin(top5_menores)] if selected == "ALL" else df_v[df_v["nombre_completo"] == selected]
    
    fig_linea = px.line(df_plot.groupby([df_plot["fecha"].dt.month, "nombre_completo"]).size().reset_index(name="v"), 
                        x="fecha", y="v", color="nombre_completo", markers=True, template="plotly_white")
    fig_tarta = px.pie(df_plot.groupby("zona_nombre").size().reset_index(name="v"), names="zona_nombre", values="v", hole=0.4)

    # Zonas
    top_zonas = df_v.groupby("zona_nombre").size().nlargest(5).index
    res_zonas = [{"zona_nombre": z, "dia_nombre": df_v[df_v["zona_nombre"]==z]["dia_nombre"].mode()[0], "visitas": len(df_v[df_v["zona_nombre"]==z])} for z in top_zonas]

    # Permanencia
    df_perm = df_v[df_v["duracion_mins"] > 5]
    fig_perm = px.bar(df_perm.groupby("nombre_completo").size().reset_index(name="casos"), x="nombre_completo", y="casos", color_discrete_sequence=[ROJO])

    # Info
    tarjeta = html.Div([html.B(f"Sujeto: {selected}"), html.Br(), f"Responsable: {df_plot.iloc[0]['adulto']}"]) if selected != "ALL" and not df_plot.empty else html.P("Viendo Top 5")

    return opciones, fig_linea, fig_tarta, tarjeta, res_zonas, fig_perm

@app.callback(
    Output("tabla-alertas", "data"),
    [Input("filtro-tabla-menor", "value"),
     Input("filtro-tabla-estado", "value")]
)
def filtrar_tabla(nombre, estado):
    dff = df_historial.copy()
    if nombre != "ALL": dff = dff[dff["nombre"] == nombre]
    if estado != "ALL": dff = dff[dff["estado"] == estado]
    return dff.to_dict("records")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run_server(host="0.0.0.0", port=port, debug=False)