import dash
from dash import html

# App Dash mínima
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Dashboard Alertas Niños"),
    html.P("Aquí podrás conectar tu consulta a BigQuery más adelante."),
])

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8080)