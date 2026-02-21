import dash
from dash import html, dcc
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
import os

# 1. INICIALIZACIÓN (Crítico: faltaba esto)
app = dash.Dash(__name__)
server = app.server # Esto es lo que usará Gunicorn

# 2. OBTENCIÓN DE DATOS Y CREACIÓN DE FIG (Crítico: faltaba esto)
def get_data():
    try:
        client = bigquery.Client()
        # Reemplaza con tu consulta real
        query = """
            SELECT id_menor, count(*) as alertas 
            FROM `tu-proyecto.tu_dataset.tu_tabla` 
            GROUP BY id_menor 
            ORDER BY alertas DESC 
            LIMIT 10
        """
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"Error BigQuery: {e}")
        # Retorno de emergencia para que la app no muera si falla la conexión
        return pd.DataFrame({"id_menor": ["Sin datos"], "alertas": [0]})

df_alertas = get_data()
fig = px.bar(df_alertas, x="id_menor", y="alertas", title="Alertas por Niño")

# 3. LAYOUT (Tu diseño corregido)
app.layout = html.Div(
    style={
        "backgroundColor": "#f4f6fb",
        "minHeight": "100vh",
        "padding": "20px",
        "fontFamily": "Arial"
    },
    children=[
        html.Div(
            style={
                "backgroundColor": "#ffffff",
                "padding": "20px",
                "borderRadius": "12px",
                "boxShadow": "0 4px 10px rgba(0,0,0,0.08)",
                "marginBottom": "20px"
            },
            children=[
                html.H1(
                    "SafeChild Guardian AI - Panel de Alertas",
                    style={"margin": "0", "color": "#1f2d3d", "textAlign": "center"}
                )
            ]
        ),
        html.Div(
            style={
                "backgroundColor": "#ffffff",
                "padding": "20px",
                "borderRadius": "12px",
                "boxShadow": "0 4px 10px rgba(0,0,0,0.08)"
            },
            children=[
                html.H3("Top 10 niños con más alertas", style={"color": "#334e68"}),
                dcc.Graph(figure=fig) # Ahora fig sí existe
            ]
        )
    ]
)

if __name__ == "__main__":
    # Cloud Run usa la variable PORT
    port = int(os.environ.get("PORT", 8080))
    app.run_server(host="0.0.0.0", port=port, debug=False)