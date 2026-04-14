import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime

app = dash.Dash(__name__)
app.title = "📈 Stock & Crypto Analytics Dashboard"

# ----------- Layout -----------
app.layout = html.Div([
    html.H1("📈 Stock & Crypto Analytics Dashboard",
            style={'textAlign': 'center', 'color': 'white'}),

    html.Div([
        html.Div([
            html.Label("Ticker (comma separated):"),
            dcc.Input(id='ticker', value='AAPL,MSFT,GOOG', type='text')
        ]),

        html.Div([
            html.Label("Start Date:"),
            dcc.DatePickerSingle(id='start', date='2023-01-01')
        ]),

        html.Div([
            html.Label("End Date:"),
            dcc.DatePickerSingle(id='end', date=pd.Timestamp.today())
        ])
    ], style={'display': 'flex', 'gap': '20px', 'color': 'white'}),

    html.Br(),

    dcc.Loading([
        dcc.Graph(id='price-chart'),
        dcc.Graph(id='volume-chart'),
        dcc.Graph(id='returns-chart'),
        dcc.Graph(id='heatmap-chart')
    ])
], style={'backgroundColor': '#000', 'padding': '20px', 'minHeight': '100vh'})


# ----------- Callback -----------
@app.callback(
    [Output('price-chart', 'figure'),
     Output('volume-chart', 'figure'),
     Output('returns-chart', 'figure'),
     Output('heatmap-chart', 'figure')],
    [Input('ticker', 'value'),
     Input('start', 'date'),
     Input('end', 'date')]
)
def update_dashboard(tickers, start, end):
    start = pd.to_datetime(start).date()
    end = pd.to_datetime(end).date()

    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    try:
        data = yf.download(ticker_list, start=start, end=end)

        if data.empty:
            raise ValueError("No data found")

        # ----------- Multi-stock Adj Close -----------
        close = data['Adj Close']

        # ----------- Moving Averages for first stock -----------
        main_stock = ticker_list[0]
        df_main = close[main_stock].to_frame(name='Adj Close')
        df_main['MA20'] = df_main['Adj Close'].rolling(20).mean()
        df_main['MA50'] = df_main['Adj Close'].rolling(50).mean()

        # ----------- Price Chart -----------
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_main.index, y=df_main['Adj Close'], name='Price'))
        fig1.add_trace(go.Scatter(x=df_main.index, y=df_main['MA20'], name='MA20'))
        fig1.add_trace(go.Scatter(x=df_main.index, y=df_main['MA50'], name='MA50'))

        fig1.update_layout(title=f"{main_stock} Price with Moving Averages",
                           template='plotly_dark')

        # ----------- Volume -----------
        volume = data['Volume'][main_stock]
        fig2 = px.bar(x=volume.index, y=volume,
                      title=f"{main_stock} Volume",
                      template='plotly_dark')

        # ----------- Returns Line Chart -----------
        returns = close.pct_change()
        fig3 = px.line(returns, title="Daily Returns Comparison",
                       template='plotly_dark')

        # ----------- Heatmap (NEW - Multi Stock Correlation) -----------
        corr = returns.corr()

        fig4 = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale='RdBu',
            title='Stock Correlation Heatmap',
            template='plotly_dark'
        )

        return fig1, fig2, fig3, fig4

    except Exception as e:
        fig = px.scatter(title=f"Error: {str(e)}", template="plotly_dark")
        return fig, fig, fig, fig


# ----------- Run App -----------
if __name__ == '__main__':
    app.run(debug=True, port=8051)
