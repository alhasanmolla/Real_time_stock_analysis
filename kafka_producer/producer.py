import yfinance as yf
from kafka import KafkaProducer
import json, time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

while True:
    data = yf.download(tickers="AAPL", period="1d", interval="1m").tail(1)
    if not data.empty:
        record = {
            "timestamp": str(data.index[0]),
            "open": float(data["Open"].iloc[0]),
            "high": float(data["High"].iloc[0]),
            "low": float(data["Low"].iloc[0]),
            "close": float(data["Close"].iloc[0]),
            "volume": int(data["Volume"].iloc[0])
        }
        producer.send('kap', record)
        print(f"Sent: {record}")
    time.sleep(60)
