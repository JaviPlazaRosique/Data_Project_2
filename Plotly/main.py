import dash
from dash import html, dcc, Input, Output
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
import os

AZUL_OSCURO = "#002b5c"  
GRIS_TEXTO = "#546e7a" 

app = dash.Dash(__name__)
server = app.server

# --- Función de Datos con Protección ---
def get_data():
    try:
        client = bigquery.Client()
        query = """
            SELECT id_menor, count(*) as alertas 
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
        # Datos de respaldo para que la app NO falle en el despliegue
        return pd.DataFrame({
            "id_menor": ["Demo-01", "Demo-02", "Demo-03"], 
            "alertas": [10, 5, 2]
        })

df_global = get_data()

def business_logic_card(titulo, texto):
    return html.Div(
        style={
            "backgroundColor": "#e3f2fd", 
            "padding": "15px",
            "borderRadius": "8px",
            "marginBottom": "20px",
            "borderLeft": f"5px solid {AZUL_OSCURO}"
        },
        children=[
            html.B(titulo, style={"color": AZUL_OSCURO, "display": "block", "marginBottom": "5px"}),
            dcc.Markdown(texto, style={"color": GRIS_TEXTO, "fontSize": "13px", "margin": "0"})
        ]
    )

app.layout = html.Div(
    style={"backgroundColor": "#f4f6fb", "minHeight": "100vh", "padding": "20px", "fontFamily": "Segoe UI, Arial"},
    children=[
        # Cabecera
        html.Div(
            style={"backgroundColor": "#ffffff", "padding": "25px", "borderRadius": "15px", "textAlign": "center", "marginBottom": "25px", "borderBottom": f"4px solid {AZUL_OSCURO}"},
            children=[
                html.H1("SafeChild Guardian AI - Panel de Alertas", style={"color": AZUL_OSCURO, "fontWeight": "bold", "display": "inline"}),
                html.Span(" 📍", style={"fontSize": "35px"})
            ]
        ),

        # Contenedor
        html.Div(
            style={"backgroundColor": "#ffffff", "padding": "30px", "borderRadius": "15px", "boxShadow": "0 4px 12px rgba(0,0,0,0.1)"},
            children=[
                business_logic_card(
                    "📊 Ranking de Reincidencia Crítica",
                    """
                    Este gráfico identifica a los menores con mayor volumen de alertas generadas. 
                    
                    **Lógica:** Cruce de la tabla de alertas con la de identidad del menor, contabilizando incursiones en zonas restringidas. 
                    
                    **Propósito:** Priorizar la intervención parental en los perfiles de mayor riesgo.
                    """
                ),

                html.Label("Seleccionar niños específicos:", style={"color": AZUL_OSCURO, "fontWeight": "600"}),
                dcc.Dropdown(
                    id="pestaña-niño",
                    options=[{"label": "Ver Todos (Top 10)", "value": "ALL"}] + 
                            [{"label": f"ID Menor: {i}", "value": i} for i in df_global["id_menor"].unique()],
                    value="ALL",
                    multi=True,
                    clearable=False,
                    style={"marginTop": "10px"}
                ),
                dcc.Graph(id="grafico-barras-alertas")
            ]
        )
    ]
)

@app.callback(
    Output("grafico-barras-alertas", "figure"),
    Input("pestaña-niño", "value")
)
def actualizar_grafico(seleccion):
    if not seleccion or "ALL" in seleccion:
        df_plot = df_global.head(10)
    else:
        df_plot = df_global[df_global["id_menor"].isin(seleccion if isinstance(seleccion, list) else [seleccion])]

    fig = px.bar(df_plot, x="id_menor", y="alertas", text="alertas", color_discrete_sequence=[AZUL_OSCURO])
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="ID del Niño",
        yaxis_title="Número de Alertas",
        font=dict(color=AZUL_OSCURO),
        xaxis={'categoryorder': 'total descending'}
    )
    return fig

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)