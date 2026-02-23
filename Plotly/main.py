import dash
from dash import dcc, html, Input, Output, dash_table, State
import pandas as pd
import os
import plotly.express as px
from google.cloud import bigquery


PROJECT_ID = os.getenv("PROJECT_ID")
client = bigquery.Client(project=PROJECT_ID)

dark_theme = {
    'background': '#0f0f0f',
    'paper': "#1e1e1e",
    'text': '#ffffff',
    'accent': "#00d4ff",
    'danger': "#ff4d4d",
    'warning': "#ffaa00",
    'subtle': "#b3b3b3",
    'info_bg': "rgba(0, 212, 255, 0.05)"
}

card_style = {
    'backgroundColor': dark_theme['paper'],
    'color': dark_theme['text'],
    'padding': '20px',
    'borderRadius': '15px',
    'boxShadow': '0 4px 15px 0 rgba(0,212,255,0.1)',
    'textAlign': 'center',
    'flex': '1',
    'margin': '10px',
    'minWidth': '180px',
    'borderTop': f'4px solid {dark_theme["accent"]}'
}

section_title_style = {
    'color': dark_theme['accent'],
    'textTransform': 'uppercase',
    'letterSpacing': '2px',
    'fontSize': '1.2rem',
    'borderBottom': f'1px solid {dark_theme["accent"]}',
    'paddingBottom': '10px',
    'marginBottom': '20px'
}

info_box_style = {
    'backgroundColor': dark_theme['info_bg'],
    'color': dark_theme['accent'],
    'padding': '15px',
    'borderRadius': '10px',
    'fontSize': '0.9rem',
    'marginTop': '10px',
    'border': f'1px solid {dark_theme["accent"]}'
}

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
    return df.iloc[0].to_dict() if not df.empty else {}

def obtener_datos_graficos():
    query = f"""
        SELECT 
            CONCAT(m.nombre, ' ', m.apellidos) as nombre_completo,
            m.discapacidad,
            m.id as id_nino,
            m.direccion as ubicacion,
            CONCAT(a.nombre, ' ', a.apellidos) as nombre_tutor,
            COUNTIF(h.estado = 'PELIGRO') as peligros,
            COUNTIF(h.estado = 'ADVERTENCIA') as advertencias
        FROM `{PROJECT_ID}.monitoreo_dataset.public_menores` m
        JOIN `{PROJECT_ID}.monitoreo_dataset.public_adultos` a ON m.id_adulto = a.id
        LEFT JOIN `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones` h ON m.id = h.id_menor
        GROUP BY 1, 2, 3, 4, 5
    """
    return ejecutar_query(query)

def obtener_zonas_frecuentes(tipo_estado):
    query = f"""
        SELECT z.nombre as zona, COUNT(h.id) as frecuencia
        FROM `{PROJECT_ID}.monitoreo_dataset.public_zonas_restringidas` z
        JOIN `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones` h ON z.id_menor = h.id_menor
        WHERE h.estado = '{tipo_estado}'
        GROUP BY 1
        ORDER BY frecuencia DESC
    """
    return ejecutar_query(query)

def obtener_tendencia_2026(id_nino="ALL"):
    filtro_nino = f"AND id_menor = '{id_nino}'" if id_nino != "ALL" else ""
    query = f"""
        SELECT EXTRACT(DAY FROM fecha) as periodo, COUNT(*) as incidentes
        FROM `{PROJECT_ID}.monitoreo_dataset.historico_notificaciones`
        WHERE EXTRACT(YEAR FROM fecha) = 2026 
        GROUP BY 1 ORDER BY 1
    """
    return ejecutar_query(query)

app = dash.Dash(__name__)
server = app.server 

app.layout = html.Div(style={'backgroundColor': dark_theme['background'], 'color': dark_theme['text'], 'minHeight': '100vh', 'padding': '40px', 'fontFamily': 'Segoe UI, sans-serif'}, children=[
    
    html.Div([
        html.H1("SISTEMA DE MONITOREO", style={'color': '#ffffff', 'margin': '0', 'fontWeight': '800', 'fontSize': '3rem'}),
        html.P("PANEL DE CONTROL ADMINISTRATIVO", style={'color': dark_theme['accent'], 'letterSpacing': '5px', 'fontWeight': '300'})
    ], style={'marginBottom': '50px'}),

    html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'marginBottom': '40px'}, children=[
        html.Div([html.P("ADULTOS"), html.H2(id="kpi-adultos")], style=card_style),
        html.Div([html.P("NIÑOS TOTALES"), html.H2(id="kpi-ninos")], style=card_style),
        html.Div([html.P("NIÑOS CON ALERTA"), html.H2(id="kpi-ninos-alerta", style={'color': dark_theme['danger']})], style=card_style),
        html.Div([html.P("PELIGROS TOTALES"), html.H2(id="kpi-alarmas", style={'color': dark_theme['danger']})], style=card_style),
        html.Div([html.P("ADVERTENCIAS"), html.H2(id="kpi-advertencias", style={'color': dark_theme['warning']})], style=card_style),
    ]),

    html.Div(style={'backgroundColor': dark_theme['paper'], 'padding': '30px', 'borderRadius': '15px', 'marginBottom': '40px'}, children=[
        html.H3("Ficha de Seguridad Individual", style=section_title_style),
        dcc.Dropdown(id='selector-detalle', placeholder="Buscar niño...", style={'color': '#000'}),
        html.Div(id='ficha-nino', style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '20px', 'marginTop': '20px'})
    ]),
    
    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px', 'marginBottom': '40px'}, children=[
        html.Div(style={'flex': '1', 'backgroundColor': dark_theme['paper'], 'borderRadius': '15px', 'padding': '25px'}, children=[
            html.H3("Ranking de Peligros Críticos", style=section_title_style),
            dcc.Graph(id='grafico-peligro', config={'displayModeBar': False}),
            html.Div("Incidentes en zonas de peligro extremo.", style=info_box_style)
        ]),
        html.Div(style={'flex': '1', 'backgroundColor': dark_theme['paper'], 'borderRadius': '15px', 'padding': '25px'}, children=[
            html.H3("Ranking de Advertencias", style=section_title_style),
            dcc.Graph(id='grafico-advertencia', config={'displayModeBar': False}),
            html.Div("Avisos preventivos frecuentes.", style=info_box_style)
        ]),
    ]),

    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px', 'marginBottom': '40px'}, children=[
        html.Div(style={'flex': '1', 'backgroundColor': dark_theme['paper'], 'borderRadius': '15px', 'padding': '25px'}, children=[
            html.H3("Zonas de Peligro Frecuentes", style=section_title_style),
            dcc.Graph(id='tarta-peligro', config={'displayModeBar': False}),
        ]),
        html.Div(style={'flex': '1', 'backgroundColor': dark_theme['paper'], 'borderRadius': '15px', 'padding': '25px'}, children=[
            html.H3("Zonas de Advertencia Frecuentes", style=section_title_style),
            dcc.Graph(id='tarta-advertencia', config={'displayModeBar': False}),
        ]),
    ]),

    html.Div(style={'backgroundColor': dark_theme['paper'], 'borderRadius': '15px', 'padding': '25px', 'marginBottom': '40px'}, children=[
        html.H3("Evolución de Incidentes - Año 2026", style=section_title_style),
        dcc.Graph(id='grafico-tendencia-2026', config={'displayModeBar': False}),
        html.Div("Seguimiento diario del volumen de alertas registradas durante el año en curso.", style=info_box_style)
    ]),

    dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0)
])

# ---- CALLBACKS ----
@app.callback(
    [Output('kpi-adultos', 'children'), Output('kpi-ninos', 'children'), Output('kpi-ninos-alerta', 'children'),
     Output('kpi-alarmas', 'children'), Output('kpi-advertencias', 'children'), Output('grafico-peligro', 'figure'),
     Output('grafico-advertencia', 'figure'), Output('tarta-peligro', 'figure'), Output('tarta-advertencia', 'figure'),
     Output('selector-detalle', 'options'), Output('grafico-tendencia-2026', 'figure')],
    [Input('interval-component', 'n_intervals'), Input('selector-detalle', 'value')]
)
def update_main_data(n, id_nino_seleccionado):
    kpis = obtener_kpis()
    df = obtener_datos_graficos()
    df_zonas_p = obtener_zonas_frecuentes('PELIGRO')
    df_zonas_a = obtener_zonas_frecuentes('ADVERTENCIA')
    id_filtro = id_nino_seleccionado if id_nino_seleccionado else "ALL"
    df_2026 = obtener_tendencia_2026(id_filtro)

    def crear_barra(df_sub, y_col, color):
        if df_sub.empty or df_sub[y_col].sum() == 0:
            return px.bar(title="Sin datos registrados").update_layout(template='plotly_dark')
        return px.bar(df_sub.sort_values(y_col, ascending=False), x='nombre_completo', y=y_col, color_discrete_sequence=[color]).update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    fig_p = crear_barra(df, 'peligros', dark_theme['danger'])
    fig_a = crear_barra(df, 'advertencias', dark_theme['warning'])
    
    fig_tarta_p = px.pie(df_zonas_p, values='frecuencia', names='zona', hole=.4, color_discrete_sequence=px.colors.sequential.Reds_r).update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    fig_tarta_a = px.pie(df_zonas_a, values='frecuencia', names='zona', hole=.4, color_discrete_sequence=px.colors.sequential.Oranges_r).update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')

    if df_2026.empty:
        fig_2026 = px.area(title="No hay registros en 2026").update_layout(template='plotly_dark')
    else:
        fig_2026 = px.area(df_2026, x='periodo', y='incidentes', color_discrete_sequence=[dark_theme['accent']]).update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    options = [{"label": row['nombre_completo'], "value": row['id_nino']} for _, row in df.iterrows()]

    return (kpis.get('adultos', 0), kpis.get('ninos_totales', 0), kpis.get('ninos_con_alerta', 0), kpis.get('alarmas', 0), kpis.get('advertencias', 0), fig_p, fig_a, fig_tarta_p, fig_tarta_a, options, fig_2026)

@app.callback(Output('ficha-nino', 'children'), [Input('selector-detalle', 'value')])
def mostrar_ficha(id_nino):
    if not id_nino: return html.P("Seleccione un menor para ver su información.")
    df = obtener_datos_graficos()
    nino = df[df['id_nino'] == id_nino].iloc[0]
    def info_item(label, value):
        return html.Div([html.P(label, style={'color': dark_theme['accent'], 'fontSize': '0.8rem', 'margin': '0'}), html.H4(str(value), style={'margin': '5px 0 0 0'})], style={'padding': '15px', 'backgroundColor': 'rgba(255,255,255,0.03)', 'borderRadius': '8px'})
    return [info_item("NOMBRE COMPLETO", nino['nombre_completo']), info_item("TUTOR LEGAL", nino['nombre_tutor']), info_item("DIRECCIÓN", nino['ubicacion']), info_item("ID", nino['id_nino']), info_item("DISCAPACIDAD", "SÍ" if nino['discapacidad'] else "NO")]

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))