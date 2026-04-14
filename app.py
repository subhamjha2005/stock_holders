import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

app = dash.Dash(__name__)
app.title = "📈 Stock & Crypto Analytics Dashboard"

# ----------- Layout -----------
app.layout = html.Div([
    html.H1("📈 Stock & Crypto Analytics Dashboard",
            style={'textAlign': 'center', 'color': 'white'}),

    html.Div([
        html.Div([
            html.Label("Ticker (comma separated):"),
            dcc.Input(id='ticker', value='AAPL,MSFT,GOOG',
                      type='text', style={'width': '200px'})
        ]),

        html.Div([
            html.Label("Start Date:"),
            dcc.DatePickerSingle(id='start', date='2023-01-01')
        ]),

        html.Div([
            html.Label("End Date:"),
            dcc.DatePickerSingle(
                id='end',
                date=pd.Timestamp.today().strftime('%Y-%m-%d')
            )
        ]),

        html.Button("Analyze", id='analyze-btn',
                    style={'height': '40px', 'marginTop': '20px'})
    ],
    style={'display': 'flex', 'gap': '20px',
           'color': 'white', 'alignItems': 'center'}),

    html.Br(),

    dcc.Loading([
        dcc.Graph(id='price-chart'),
        dcc.Graph(id='volume-chart'),
        dcc.Graph(id='returns-chart'),
        dcc.Graph(id='heatmap-chart')
    ])
], style={'backgroundColor': '#000',
          'padding': '20px',
          'minHeight': '100vh'})


# ----------- Callback -----------
@app.callback(
    [Output('price-chart', 'figure'),
     Output('volume-chart', 'figure'),
     Output('returns-chart', 'figure'),
     Output('heatmap-chart', 'figure')],
    Input('analyze-btn', 'n_clicks'),
    [State('ticker', 'value'),
     State('start', 'date'),
     State('end', 'date')]
)
def update_dashboard(n_clicks, tickers, start, end):

    if not n_clicks:
        return [go.Figure()] * 4

    try:
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        ticker_list = [t.strip().upper()
                       for t in tickers.split(",") if t.strip()]

        if not ticker_list:
            raise ValueError("Please enter at least one ticker")

        # ----------- Download Data -----------
        data = yf.download(
            ticker_list,
            start=start,
            end=end,
            group_by='ticker',
            auto_adjust=False,
            progress=False
        )

        if data.empty:
            raise ValueError("No data found")

        # ----------- FIX: Close Extraction -----------
        if isinstance(data.columns, pd.MultiIndex):
            # Multi ticker
            if 'Adj Close' in data.columns.get_level_values(1):
                close_df = data.xs('Adj Close', level=1, axis=1)
            else:
                close_df = data.xs('Close', level=1, axis=1)
        else:
            # Single ticker
            col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            close_df = data[[col]].copy()
            close_df.columns = [ticker_list[0]]

        close_df.dropna(how='all', inplace=True)

        # ----------- Main Stock -----------
        main_stock = ticker_list[0]

        df_main = close_df[[main_stock]].copy()
        df_main['MA20'] = df_main[main_stock].rolling(20).mean()
        df_main['MA50'] = df_main[main_stock].rolling(50).mean()

        # ----------- Price Chart -----------
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_main.index,
                                 y=df_main[main_stock],
                                 name='Price'))
        fig1.add_trace(go.Scatter(x=df_main.index,
                                 y=df_main['MA20'],
                                 name='MA20'))
        fig1.add_trace(go.Scatter(x=df_main.index,
                                 y=df_main['MA50'],
                                 name='MA50'))

        fig1.update_layout(
            title=f"{main_stock} Price + Moving Averages",
            template='plotly_dark'
        )

        # ----------- FIX: Volume -----------
        if isinstance(data.columns, pd.MultiIndex):
            volume = data[main_stock]['Volume']
        else:
            volume = data['Volume']

        fig2 = px.bar(
            x=volume.index,
            y=volume,
            title=f"{main_stock} Volume",
            template='plotly_dark'
        )

        # ----------- Returns -----------
        returns = close_df.pct_change().dropna()

        fig3 = px.line(
            returns,
            title="Daily Returns Comparison",
            template='plotly_dark'
        )

        # ----------- Heatmap -----------
        corr = returns.corr()

        fig4 = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale='RdBu',
            title='Correlation Heatmap',
            template='plotly_dark'
        )

        return fig1, fig2, fig3, fig4

    except Exception as e:
        fig = px.scatter(
            title=f"Error: {str(e)}",
            template="plotly_dark"
        )
        return fig, fig, fig, fig


# ----------- Run -----------
if __name__ == '__main__':
    app.run(debug=True, port=8051)
