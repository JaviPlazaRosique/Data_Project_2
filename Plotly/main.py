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

    total_menores = 0
    try:
        query_menores = f"SELECT count(*) as total FROM `{project_id}.{dataset_id}.menores`"
        df_menores = client.query(query_menores).to_dataframe()
        if not df_menores.empty:
            total_menores = df_menores['total'][0]
    except Exception:
        if not df_notificaciones.empty:
            total_menores = df_notificaciones['id_menor'].nunique()

    return df_notificaciones, total_menores

style_container = {
    'font-family': '"Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    'padding': '20px',
    'background-color': '#f5f5f5',
    'min-height': '100vh'
}

app.layout = html.Div(style=style_container, children=[
    html.H1("Dashboard de Administración - Monitoreo de Menores", 
            style={'text-align': 'center', 'color': '#333', 'margin-bottom': '30px'}),
    
    html.Div(style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px', 'margin-bottom': '30px'}, children=[
        html.Div(style={'flex': '1', 'min-width': '400px', 'background': 'white', 'padding': '15px', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
            html.H3("Distribución de Alertas", style={'text-align': 'center', 'color': '#555'}),
            dcc.Dropdown(id='dropdown-menor', placeholder="Selecciona un menor", clearable=True, style={'margin-bottom': '10px'}),
            dcc.Graph(id='grafico-estados')
        ]),
        html.Div(style={'flex': '1', 'min-width': '400px', 'background': 'white', 'padding': '15px', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
            html.H3("Mapa de Incidencias", style={'text-align': 'center', 'color': '#555'}),
            dcc.Graph(id='mapa-alertas')
        ]),
    ]),
    
    html.Div(style={'background': 'white', 'padding': '15px', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
        html.H3("Top 5 Menores con más Alertas (Peligro/Advertencia)", style={'text-align': 'center', 'color': '#555'}),
        dcc.Graph(id='grafico-top5')
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=60*1000, 
        n_intervals=0
    )
])

@app.callback(
    [Output('grafico-estados', 'figure'),
     Output('mapa-alertas', 'figure'),
     Output('grafico-top5', 'figure'),
     Output('dropdown-menor', 'options')],
    [Input('interval-component', 'n_intervals'),
     Input('dropdown-menor', 'value')]
)
def update_dashboard(n, selected_menor):
    df, total_menores = get_data()
    
    fig_estados = px.pie(title="Sin datos")
    fig_mapa = px.scatter_mapbox(lat=[], lon=[], zoom=1)
    fig_mapa.update_layout(mapbox_style="open-street-map")
    fig_top5 = px.bar(title="Sin datos")
    options = []

    if not df.empty:
        options = [{'label': i, 'value': i} for i in df['nombre_menor'].unique()]
        
        df_alerts = df[df['estado'].isin(['PELIGRO', 'ADVERTENCIA'])]
        if not df_alerts.empty:
            top5 = df_alerts['nombre_menor'].value_counts().head(5).reset_index()
            top5.columns = ['nombre_menor', 'cantidad']
            fig_top5 = px.bar(top5, x='nombre_menor', y='cantidad', 
                              color='cantidad', color_continuous_scale='Reds')
        
        if selected_menor:
            df = df[df['nombre_menor'] == selected_menor]

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

    return fig_estados, fig_mapa, fig_top5, options

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host="0.0.0.0", port=port)
