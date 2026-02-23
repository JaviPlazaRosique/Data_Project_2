import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from google.cloud import bigquery

app = dash.Dash(__name__)
server = app.server

project_id = os.getenv("PROJECT_ID")
client = bigquery.Client(project=project_id)
dataset_id = "monitoreo_dataset"

def get_data():
    """Consulta datos de BigQuery para los KPIs y gráficos."""
    
    # Consulta 1: Histórico de notificaciones (últimas 24 horas)
    query_notificaciones = f"""
        SELECT 
            id_menor, 
            nombre_menor, 
            latitud, 
            longitud, 
            fecha, 
            estado 
        FROM `{project_id}.{dataset_id}.historico_notificaciones`
        WHERE fecha >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        ORDER BY fecha DESC
    """
    
    try:
        df_notificaciones = client.query(query_notificaciones).to_dataframe()
    except Exception as e:
        print(f"Error consultando notificaciones: {e}")
        df_notificaciones = pd.DataFrame(columns=['id_menor', 'nombre_menor', 'latitud', 'longitud', 'fecha', 'estado'])

    # Consulta 2: Total de menores monitoreados
    # Intentamos leer de la tabla 'menores' replicada por Datastream.
    total_menores = 0
    try:
        query_menores = f"SELECT count(*) as total FROM `{project_id}.{dataset_id}.menores`"
        df_menores = client.query(query_menores).to_dataframe()
        if not df_menores.empty:
            total_menores = df_menores['total'][0]
    except Exception:
        # Fallback: contar IDs únicos en notificaciones si la tabla menores no está disponible
        if not df_notificaciones.empty:
            total_menores = df_notificaciones['id_menor'].nunique()

    return df_notificaciones, total_menores

# Estilos CSS
style_card = {
    'border': '1px solid #e0e0e0',
    'padding': '20px',
    'border-radius': '8px',
    'background-color': 'white',
    'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
    'text-align': 'center',
    'flex': '1',
    'margin': '0 10px'
}

style_container = {
    'font-family': '"Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    'padding': '20px',
    'background-color': '#f5f5f5',
    'min-height': '100vh'
}

app.layout = html.Div(style=style_container, children=[
    html.H1("Dashboard de Administración - Monitoreo de Menores", 
            style={'text-align': 'center', 'color': '#333', 'margin-bottom': '30px'}),
    
    html.Div(style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '30px'}, children=[
        html.Div(style=style_card, children=[
            html.H3("Total Menores", style={'color': '#7f8c8d', 'font-size': '1.2rem'}),
            html.H2(id='kpi-menores', style={'color': '#2980b9', 'font-size': '2.5rem', 'margin': '10px 0'})
        ]),
        html.Div(style=style_card, children=[
            html.H3("Alertas (24h)", style={'color': '#7f8c8d', 'font-size': '1.2rem'}),
            html.H2(id='kpi-alertas', style={'color': '#f39c12', 'font-size': '2.5rem', 'margin': '10px 0'})
        ]),
        html.Div(style=style_card, children=[
            html.H3("Peligros Críticos", style={'color': '#7f8c8d', 'font-size': '1.2rem'}),
            html.H2(id='kpi-peligros', style={'color': '#c0392b', 'font-size': '2.5rem', 'margin': '10px 0'})
        ]),
    ]),

    html.Div(style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px', 'margin-bottom': '30px'}, children=[
        html.Div(style={'flex': '1', 'min-width': '400px', 'background': 'white', 'padding': '15px', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
            html.H3("Distribución de Alertas", style={'text-align': 'center', 'color': '#555'}),
            dcc.Graph(id='grafico-estados')
        ]),
        html.Div(style={'flex': '1', 'min-width': '400px', 'background': 'white', 'padding': '15px', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
            html.H3("Mapa de Incidencias", style={'text-align': 'center', 'color': '#555'}),
            dcc.Graph(id='mapa-alertas')
        ]),
    ]),
    
    html.Div(style={'background': 'white', 'padding': '20px', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
        html.H3("Últimas 10 Notificaciones", style={'color': '#555', 'margin-bottom': '15px'}),
        html.Div(id='tabla-notificaciones', style={'overflow-x': 'auto'})
    ]),

    dcc.Interval(
        id='interval-component',
        interval=60*1000, 
        n_intervals=0
    )
])

@app.callback(
    [Output('kpi-menores', 'children'),
     Output('kpi-alertas', 'children'),
     Output('kpi-peligros', 'children'),
     Output('grafico-estados', 'figure'),
     Output('mapa-alertas', 'figure'),
     Output('tabla-notificaciones', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    df, total_menores = get_data()
    
    total_alertas = 0
    total_peligros = 0
    fig_estados = px.pie(title="Sin datos")
    fig_mapa = px.scatter_mapbox(lat=[], lon=[], zoom=1)
    fig_mapa.update_layout(mapbox_style="open-street-map")
    tabla_html = html.P("No hay datos disponibles.")

    if not df.empty:
        total_alertas = len(df)
        total_peligros = len(df[df['estado'] == 'PELIGRO'])
        
        fig_estados = px.pie(df, names='estado', hole=0.4,
                             color='estado',
                             color_discrete_map={'PELIGRO': '#c0392b', 'ADVERTENCIA': '#f39c12', 'OK': '#27ae60'})
        fig_estados.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        fig_mapa = px.scatter_mapbox(df, lat="latitud", lon="longitud", color="estado",
                                     hover_name="nombre_menor", hover_data=["fecha", "estado"],
                                     color_discrete_map={'PELIGRO': '#c0392b', 'ADVERTENCIA': '#f39c12', 'OK': '#27ae60'},
                                     zoom=5)
        fig_mapa.update_layout(mapbox_style="carto-positron")
        fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        df_tabla = df.head(10)[['fecha', 'nombre_menor', 'estado', 'latitud', 'longitud']]

        try:
            df_tabla['fecha'] = df_tabla['fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass

        header = [html.Tr([html.Th(col, style={'padding': '10px', 'text-align': 'left', 'border-bottom': '2px solid #ddd'}) for col in df_tabla.columns])]
        rows = []
        for i in range(len(df_tabla)):
            row_style = {'background-color': '#f9f9f9'} if i % 2 == 0 else {}
            cells = [html.Td(df_tabla.iloc[i][col], style={'padding': '10px', 'border-bottom': '1px solid #eee'}) for col in df_tabla.columns]
            rows.append(html.Tr(cells, style=row_style))
        
        tabla_html = html.Table(header + rows, style={'width': '100%', 'border-collapse': 'collapse'})

    return total_menores, total_alertas, total_peligros, fig_estados, fig_mapa, tabla_html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host="0.0.0.0", port=port)
