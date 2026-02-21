import dash
from dash import html, dcc
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
import os

project_id = os.environ.get("ID_PROYECTO", "gemma-12")
port = int(os.environ.get("PORT", "8080"))

app = dash.Dash(__name__)


try:
    client = bigquery.Client(project=project_id)
    
    query = f"""
    SELECT id_menor, COUNT(*) as alertas
    FROM `{project_id}.monitoreo_dataset.historico_ubicacion`
    GROUP BY id_menor
    ORDER BY alertas DESC
    LIMIT 10
    """
    
    df = client.query(query).to_dataframe()
    fig = px.bar(df, x="id_menor", y="alertas", title="Top 10 niños con más alertas")
    
except Exception as e:
    print(f"Error fetching data from BigQuery: {e}")
    fig = {
        "data": [],
        "layout": {
            "title": "Error al cargar datos - Dashboard inicializándose",
            "xaxis": {"title": "id_menor"},
            "yaxis": {"title": "alertas"}
        }
    }

app.layout = html.Div([
    html.H1("Dashboard Alertas Niños"),
    html.P("Número de alertas por niño"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=False)
    