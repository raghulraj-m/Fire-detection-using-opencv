import yfinance as yf
import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from sklearn.linear_model import LinearRegression
import plotly.express as px
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import textwrap
from flask import Flask, request, jsonify
import numpy as np

warnings.filterwarnings("ignore")

# Function to get stock data
def get_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data

# Function to perform linear regression and forecast
def perform_linear_regression(stock_data):
    stock_data['Date'] = stock_data.index
    stock_data['Days'] = (stock_data['Date'] - stock_data['Date'].min()).dt.days
    X = stock_data[['Days']].values
    y = stock_data['Close'].values

    model = LinearRegression()
    model.fit(X, y)

    # Forecast for the next 30 days
    future_days = pd.DataFrame({'Days': range(stock_data['Days'].max() + 1, stock_data['Days'].max() + 31)})
    forecast = model.predict(future_days[['Days']])
    forecast_dates = pd.date_range(start=stock_data.index[-1] + pd.DateOffset(1), periods=30)

    return forecast_dates, forecast

# Set up the Dash web application
app = Dash(__name__)

# Set up the Flask application
flask_app = Flask(__name__)

@app.route('/process_user_input_bot1', methods=['POST'])
def process_user_input_bot1():
    user_message = request.json.get('userMessage')
    say = user_message
    # Add the rest of your chatbot code here
    # ...

    return jsonify({'chatbotResponse': 'Your chatbot response goes here'})

# URL of your Flask application (modify it accordingly)
FLASK_API_URL = 'http://127.0.0.1:5000'

app.layout = html.Div([
    html.H1("Stock Price Visualization and Forecasting"),
    dcc.Input(id='stock-ticker-input', type='text', value='AAPL', placeholder='Enter stock ticker'),
    dcc.DatePickerRange(
        id='date-picker-range',
        display_format='YYYY-MM-DD',
        start_date='2022-01-01',
        end_date='2023-01-01'
    ),
    dcc.Graph(id='stock-price-graph'),
    html.Div([
        dcc.Input(id='user-input', type='text', placeholder='Ask me about stocks...'),
        html.Button('Submit', id='submit-button', n_clicks=0),
        html.Div(id='chat-output')
    ])
])

@app.callback(
    [Output('stock-price-graph', 'figure'),
     Output('chat-output', 'children')],
    [Input('stock-ticker-input', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('user-input', 'value')]
)
def update_graph(ticker, start_date, end_date, n_clicks, user_input):
    stock_data = get_stock_data(ticker, start_date, end_date)
    forecast_dates, forecast = perform_linear_regression(stock_data)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=[f"{ticker} Stock Price with Moving Averages and Forecast", f"Trading Volume"])

    # Plot historical stock prices
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name='Historical Prices'), row=1, col=1)

    # Plot moving averages
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'].rolling(window=10).mean(), mode='lines', name='10-day MA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'].rolling(window=50).mean(), mode='lines', name='50-day MA'), row=1, col=1)

    # Plot forecasted prices
    fig.add_trace(go.Scatter(x=forecast_dates, y=forecast, mode='lines', name='Forecast'), row=1, col=1)

    # Plot trading volume
    fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='Trading Volume'), row=2, col=1)

    fig.update_layout(title_text=f"{ticker} Stock Price and Volume", xaxis_rangeslider_visible=True)

    # Chatbot responses
    chatbot_response = ''
    if n_clicks > 0 and user_input:
        # Communicate with the Flask API to get chatbot response
        chatbot_api_url = f"{FLASK_API_URL}/process_user_input_bot1"
        response = requests.post(chatbot_api_url, json={'userMessage': user_input})
        chatbot_response = response.json().get('chatbotResponse', '')

    return fig, chatbot_response

if __name__ == '__main__':
    flask_app.run(port=5000, debug=False, threaded=True)
    app.run_server(debug=True)
