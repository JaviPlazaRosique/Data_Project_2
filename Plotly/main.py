import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import os
from google.cloud import bigquery

# ---- CONFIGURACIÓN BQ ----
PROJECT_ID = "gemma-12" 
client = bigquery.Client(project=PROJECT_ID)

# ---- ESTILOS DEL DASHBOARD ----
dark_theme = {
    'background': '#111111',
    'paper': "#333333",  # Gris más oscuro para las tarjetas
    'text': '#ffffff',
    'accent': "#ffffff", # Título en blanco
    'danger': "#ff4d4d",
    'warning': "#ffaa00"
}

card_style = {
    'backgroundColor': dark_theme['paper'],
    'color': dark_theme['text'],
    'padding': '20px',
    'borderRadius': '10px',
    'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.3)',
    'textAlign': 'center',
    'flex': '1',
    'margin': '10px',
    'minWidth': '150px'
}

# ---- FUNCIONES PARA OBTENER LOS DATOS EN BQ ----
def ejecutar_query(query):
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        print(f"Error en BQ: {e}")
        return pd.DataFrame()

def obtener_kpis():
    query = f""" 
        SELECT
            (SELECT COUNT (*) FROM `{PROJECT_ID}.monitoreo_dataset.public_adultos`) AS adultos,
            (SELECT COUNT (*) FROM `{PROJECT_ID}.monitoreo_dataset.public_menores`) AS ninos_totales,
            (SELECT COUNT(DISTINCT id_menor) FROM `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones` WHERE estado != 'OK') as ninos_con_alerta,
            (SELECT COUNT(*) FROM `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones` WHERE estado = 'PELIGRO') as alarmas, 
            (SELECT COUNT(*) FROM `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones` WHERE estado = 'ADVERTENCIA') as advertencias
    """
    df = ejecutar_query(query)
    if not df.empty:
        return df.iloc[0].to_dict()
    return {"adultos": 0, "ninos_totales": 0, "ninos_con_alerta": 0, "alarmas": 0, "advertencias": 0}
    
    # Query para Barras: Reincidencias de Alarma y Advertencia + Datos de Padres
def obtener_datos_graficos():
    # Query para Barras: Reincidencias de Alarma y Advertencia + Datos de Padres
    query_barras = f"""
        SELECT 
            CONCAT(m.nombre, ' ', m.apellidos) as nombre_completo,
            m.discapacidad,
            CONCAT(a.nombre, ' ', a.apellidos) as nombre_padre,
            COUNTIF(h.estado = 'PELIGRO') as alarmas,
            COUNTIF(h.estado = 'ADVERTENCIA') as advertencias,
            COUNTIF(h.estado != 'OK') as total_reincidencias
        FROM `{PROJECT_ID}.monitoreo_dataset.public_menores` m
        JOIN `{PROJECT_ID}.monitoreo_dataset.public_adultos` a ON m.id_adulto = a.id
        JOIN `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones` h ON m.id = h.id_menor
        GROUP BY 1, 2, 3
        HAVING total_reincidencias > 0
        ORDER BY total_reincidencias DESC
    """
    
    # Query para Tarta: Zonas más visitadas (Alertas por zona)
    # Nota: Asumimos que el nombre de la zona se puede inferir o está vinculado
    query_tarta = f"""
        SELECT z.nombre as zona, COUNT(h.id) as visitas
        FROM `{PROJECT_ID}.monitoreo_dataset.public_zonas_restringidas` z
        JOIN `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones` h ON z.id_menor = h.id_menor
        WHERE h.estado != 'PELIGRO'
        GROUP BY 1
        ORDER BY visitas DESC
    """    
    df_barras = ejecutar_query(query_barras)
    df_tarta = ejecutar_query(query_tarta)
    
    return df_barras, df_tarta
    
# ---- APP DASH ----
app = dash.Dash(__name__)
server = app.server 

app.layout = html.Div(style={'backgroundColor': dark_theme['background'], 'color': dark_theme['text'], 'minHeight': '100vh', 'padding': '20px', 'fontFamily': 'sans-serif'}, children=[
    
    # 1. TÍTULO
    html.H1("PANEL DE ADMINISTRADORES - MONITOREO MENORES", style={'textAlign': 'left', 'color': dark_theme['accent'], 'marginBottom': '30px', 'fontWeight': 'bold'}),

    # 2. FILA DE KPIs (Números grandes)
    html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'marginBottom': '30px'}, children=[
        html.Div([html.P("Total adultos registrados", style={'fontSize': '14px'}), html.H2(id="kpi-adultos", style={'margin': '0'})], style=card_style),
        html.Div([html.P("Total niños registrados", style={'fontSize': '14px'}), html.H2(id="kpi-ninos", style={'margin': '0'})], style=card_style),
        html.Div([html.P("Niños con alerta/advertencia", style={'fontSize': '14px'}), html.H2(id="kpi-ninos-alerta", style={'color': dark_theme['danger'], 'margin': '0'})], style=card_style),
        html.Div([html.P("Total niños con alarma", style={'fontSize': '14px'}), html.H2(id="kpi-alarmas", style={'color': dark_theme['danger'], 'margin': '0'})], style=card_style),
        html.Div([html.P("Total niños con advertencia", style={'fontSize': '14px'}), html.H2(id="kpi-advertencias", style={'color': dark_theme['warning'], 'margin': '0'})], style=card_style),
    ]),

    # 3. NUEVA FILA: GRÁFICOS (Barras y Tarta)
    html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '30px'}, children=[
        # Gráfico de Barras (Reincidencia) - Ocupa más espacio (flex: 2)
        html.Div(style={'flex': '2', 'backgroundColor': 'rgba(255,255,255,0.05)', 'borderRadius': '15px', 'marginRight': '10px', 'padding': '15px'}, children=[
            dcc.Graph(id='grafico-reincidencias')
        ]),
        # Gráfico de Tarta (Zonas) - Ocupa menos (flex: 1)
        html.Div(style={'flex': '1', 'backgroundColor': 'rgba(255,255,255,0.05)', 'borderRadius': '15px', 'padding': '15px'}, children=[
            dcc.Graph(id='grafico-tarta-zonas')
        ]),
    ]),

    # 4. CONTENEDOR: EXPLORADOR DETALLADO (Filtro y Tabla)
    html.Div(style={'backgroundColor': 'rgba(255,255,255,0.05)', 'padding': '25px', 'borderRadius': '15px', 'marginBottom': '20px'}, children=[
        html.H3("Explorador Detallado de Menores", style={'marginBottom': '15px', 'fontSize': '18px'}),
        
        dcc.Dropdown(
            id='filtro-nombre',
            options=[{"label": "All Children", "value": "ALL"}],
            value='ALL',
            style={'color': '#000000', 'borderRadius': '5px'} 
        ),
        
        html.Div(style={'marginTop': '25px'}, children=[
            dash_table.DataTable(
                id='tabla-datos',
                columns=[
                    {"name": "Name", "id": "nombre"},
                    {"name": "Surname", "id": "apellidos"},
                    {"name": "Address", "id": "direccion"},
                    {"name": "Disability", "id": "discapacidad"}
                ],
                style_header={'backgroundColor': '#222', 'color': 'white', 'fontWeight': 'bold', 'border': 'none'},
                style_cell={'backgroundColor': 'transparent', 'color': 'white', 'border': 'none', 'padding': '12px', 'textAlign': 'left'},
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgba(255,255,255,0.02)'}],
                page_size=10
            )
        ])
    ]),

    # 5. COMPONENTE DE INTERVALO (Fuera de los contenedores visuales)
    dcc.Interval(id='interval-component', interval=15*1000, n_intervals=0)
])

# ---- CALLBACK ----
@app.callback(
    [Output('tabla-datos', 'data'),
     Output('filtro-nombre', 'options'),
     Output('kpi-adultos', 'children'),
     Output('kpi-ninos', 'children'),
     Output('kpi-ninos-alerta', 'children'),
     Output('kpi-alarmas', 'children'),
     Output('kpi-advertencias', 'children'),
     Output('grafico-reincidencias', 'figure'),
     Output('grafico-tarta-zonas', 'figure')],
    [Input('filtro-nombre', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_dashboard(nombre_seleccionado, n):
    # 1. Obtener Datos Base
    query_base = f"SELECT nombre, apellidos, direccion, discapacidad FROM `{PROJECT_ID}.monitoreo_dataset.public_menores`"
    if nombre_seleccionado != "ALL":
        query_base += f" WHERE nombre = '{nombre_seleccionado}'"
    
    df_tabla = ejecutar_query(query_base)
    df_nombres = ejecutar_query(f"SELECT DISTINCT nombre FROM `{PROJECT_ID}.monitoreo_dataset.public_menores`")
    
    # 2. Obtener KPIs y Gráficos (JOINS)
    kpis = obtener_kpis()
    df_barras, df_tarta = obtener_datos_graficos() 

    # 3. Construir Gráfico de Barras
    fig_barras = px.bar(
        df_barras, 
        x='nombre_completo', 
        y=['alarmas', 'advertencias'],
        title="Ranking de Reincidencia (Total Alert System)",
        barmode='group',
        color_discrete_map={'alarmas': dark_theme['danger'], 'advertencias': dark_theme['warning']},
        hover_data=['nombre_padre', 'discapacidad']
    )
    fig_barras.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 4. Construir Gráfico de Tarta
    fig_tarta = px.pie(
        df_tarta, 
        values='visitas', 
        names='zona', 
        title="Zonas Restringidas Más Visitadas",
        hole=0.4
    )
    fig_tarta.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')

    # Preparar opciones del dropdown
    opciones = [{"label": "All Children", "value": "ALL"}]
    if not df_nombres.empty:
        opciones += [{"label": n, "value": n} for n in sorted(df_nombres['nombre'].unique())]

    # Retornar todos los Outputs en el orden correcto
    return (
        df_tabla.to_dict('records'), 
        opciones,
        kpis.get('adultos', 0), 
        kpis.get('ninos_totales', 0), 
        kpis.get('ninos_con_alerta', 0), 
        kpis.get('alarmas', 0), 
        kpis.get('advertencias', 0),
        fig_barras, 
        fig_tarta
    )

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))