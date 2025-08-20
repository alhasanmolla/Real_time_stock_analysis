import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["stock_db"]
collection = db["predictions"]  # Change if your collection name is different

COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "predicted_price"]

def fetch_data():
    data = list(collection.find())
    if not data:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(data)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
    return df

TIME_FRAMES = [
    {"label": "1 Minute", "value": 1},
    {"label": "3 Minutes", "value": 3},
    {"label": "5 Minutes", "value": 5},
    {"label": "10 Minutes", "value": 10},
    {"label": "15 Minutes", "value": 15},
    {"label": "30 Minutes", "value": 30},
    {"label": "1 Hour", "value": 60},
    {"label": "2 Hours", "value": 120},
    {"label": "4 Hours", "value": 240},
    {"label": "6 Hours", "value": 360},
    {"label": "12 Hours", "value": 720},
    {"label": "24 Hours", "value": 1440},
    {"label": "1 Week", "value": 10080},
    {"label": "1 Month", "value": 43200},
    {"label": "1 Year", "value": 525600},
    {"label": "All Time", "value": 999999}  # Use a large value for all time
]

app = dash.Dash(__name__)
app.title = "Real-Time Candlestick Dashboard"

app.layout = html.Div([
    html.H1("📈 Real-Time Candlestick Dashboard AAPL", style={"textAlign": "center"}),
    html.Div([
        html.Label("Select Time Frame:"),
        dcc.Dropdown(
            id="time-frame-dropdown",
            options=TIME_FRAMES,
            value=5,
            clearable=False,
            style={"width": "200px"}
        ),
    ], style={"display": "flex", "justifyContent": "center", "alignItems": "center", "marginBottom": "20px"}),
    dcc.Graph(id="candlestick-graph"),
    dcc.Interval(
        id="interval-component",
        interval=60*1000,  # 1 minute in milliseconds
        n_intervals=0
    ),
    html.Div(id="insights", style={"marginTop": "30px", "textAlign": "center", "fontSize": "18px"})
], style={"maxWidth": "900px", "margin": "auto"})

@app.callback(
    [Output("candlestick-graph", "figure"),
     Output("insights", "children")],
    [Input("interval-component", "n_intervals"),
     Input("time-frame-dropdown", "value")]
)
def update_graph(n, time_frame_minutes):
    df = fetch_data()
    required_cols = {"timestamp", "open", "high", "low", "close"}
    if df.empty or not required_cols.issubset(df.columns):
        return go.Figure(), "No data available or missing required columns."

    # Filter to the latest N minutes
    now = df["timestamp"].max()
    min_time = now - timedelta(minutes=time_frame_minutes)
    df_window = df[df["timestamp"] >= min_time]

    if df_window.empty:
        return go.Figure(), f"No data in the last {time_frame_minutes} minutes."

    fig = go.Figure(data=[
        go.Candlestick(
            x=df_window["timestamp"],
            open=df_window["open"],
            high=df_window["high"],
            low=df_window["low"],
            close=df_window["close"],
            name="Candlestick"
        )
    ])
    fig.update_layout(
        title=f"Real-Time Candlestick Chart ({time_frame_minutes} min window)",
        xaxis_title="Timestamp",
        yaxis_title="Price",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # Example insights: show latest close, predicted price, and volume
    latest_close = df_window["close"].iloc[-1]
    latest_predicted = df_window["predicted_price"].iloc[-1] if "predicted_price" in df_window.columns else "N/A"
    latest_volume = df_window["volume"].iloc[-1] if "volume" in df_window.columns else "N/A"
    insight = (
        f"Latest Close: {latest_close:.2f} | "
        f"Predicted Price: {latest_predicted}  "
        # f"Volume: <b>{latest_volume}</b>"
    )

    return fig, insight

if __name__ == "__main__":
    app.run(debug=True, port=8050)