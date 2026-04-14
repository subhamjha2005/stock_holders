import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import yfinance as yf
import plotly.express as px
import pandas as pd
import datetime

app = dash.Dash(__name__)
app.title = "📈 Stock & Crypto Analytics Dashboard"

# ------------------ STYLES ------------------
CARD_STYLE = {
    "background": "rgba(255,255,255,0.05)",
    "backdropFilter": "blur(10px)",
    "borderRadius": "15px",
    "padding": "15px",
    "boxShadow": "0 4px 30px rgba(0,0,0,0.3)"
}

INPUT_STYLE = {
    "width": "100%",
    "padding": "10px",
    "borderRadius": "8px",
    "border": "1px solid #333",
    "backgroundColor": "#111",
    "color": "white"
}

# ------------------ LAYOUT ------------------
app.layout = html.Div([

    # Header
    html.H1(
        "📈 Stock & Crypto Analytics Dashboard",
        style={
            "textAlign": "center",
            "color": "white",
            "marginBottom": "20px",
            "fontWeight": "600"
        }
    ),

    # Controls (Premium Bar)
    html.Div([
        html.Div([
            html.Label("Ticker", style={"color": "#aaa"}),
            dcc.Input(id="ticker", value="AAPL", type="text", style=INPUT_STYLE)
        ], style={"flex": 1}),

        html.Div([
            html.Label("Start Date", style={"color": "#aaa"}),
            dcc.DatePickerSingle(id="start", date="2023-01-01")
        ], style={"flex": 1}),

        html.Div([
            html.Label("End Date", style={"color": "#aaa"}),
            dcc.DatePickerSingle(id="end", date=pd.Timestamp.today())
        ], style={"flex": 1})

    ], style={
        "display": "flex",
        "gap": "20px",
        "marginBottom": "25px",
        **CARD_STYLE
    }),

    # Charts Grid
    html.Div([

        html.Div([dcc.Graph(id="price-chart")], style=CARD_STYLE),
        html.Div([dcc.Graph(id="volume-chart")], style=CARD_STYLE),

        html.Div([dcc.Graph(id="returns-chart")], style=CARD_STYLE),
        html.Div([dcc.Graph(id="heatmap-chart")], style=CARD_STYLE)

    ], style={
        "display": "grid",
        "gridTemplateColumns": "1fr 1fr",
        "gap": "20px"
    })

], style={
    "background": "linear-gradient(135deg, #0a0a0a, #111)",
    "padding": "30px",
    "minHeight": "100vh",
    "fontFamily": "Segoe UI"
})


# ------------------ CALLBACK ------------------
@app.callback(
    [
        Output("price-chart", "figure"),
        Output("volume-chart", "figure"),
        Output("returns-chart", "figure"),
        Output("heatmap-chart", "figure"),
    ],
    [
        Input("ticker", "value"),
        Input("start", "date"),
        Input("end", "date"),
    ],
)
def update_dashboard(ticker, start, end):
    try:
        start = pd.to_datetime(start).date() if start else datetime.date(2023, 1, 1)
        end = pd.to_datetime(end).date() if end else datetime.date.today()

        data = yf.download(ticker, start=start, end=end)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data is None or data.empty or len(data) < 2:
            fig = px.scatter(title="No data available", template="plotly_dark")
            return fig, fig, fig, fig

        price_col = "Adj Close" if "Adj Close" in data.columns else "Close"

        data["Daily Return"] = data[price_col].pct_change()

        fig1 = px.line(data, x=data.index, y=price_col, template="plotly_dark")
        fig2 = px.bar(data, x=data.index, y="Volume", template="plotly_dark")
        fig3 = px.histogram(data, x="Daily Return", template="plotly_dark")

        cols = [c for c in ['Open','High','Low','Close','Adj Close','Volume'] if c in data.columns]

        if len(cols) > 1:
            corr = data[cols].corr()
            fig4 = px.imshow(corr, text_auto=True, template="plotly_dark")
        else:
            fig4 = px.scatter(title="Heatmap unavailable", template="plotly_dark")

        return fig1, fig2, fig3, fig4

    except Exception as e:
        print("ERROR:", e)
        fig = px.scatter(title=f"Error: {str(e)}", template="plotly_dark")
        return fig, fig, fig, fig


# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(debug=True, port=8051)
