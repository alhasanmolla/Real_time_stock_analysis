import findspark
findspark.init()
findspark.find()
import pyspark
# ______________________________________

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType
import pickle
from pymongo import MongoClient

# Spark Session
spark = SparkSession.builder \
    .appName("StockPrediction") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Kafka Schema
schema = StructType([
    StructField("timestamp", StringType()),
    StructField("open", FloatType()),
    StructField("high", FloatType()),
    StructField("low", FloatType()),
    StructField("close", FloatType()),
    StructField("volume", IntegerType())
])

# Read from Kafka
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "kap") \
    .load()

df_parsed = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Load ML model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

def predict_price(open_, high_, low_, close_, volume_):
    return float(model.predict([[open_, high_, low_, close_, volume_]])[0])

def write_to_mongo(df, epoch_id):
    records = df.collect()
    client = MongoClient("mongodb://localhost:27017/")
    db = client["stock_db"]
    col = db["predictions"]
    for row in records:
        prediction = predict_price(row.open, row.high, row.low, row.close, row.volume)
        col.insert_one({
            "timestamp": row.timestamp,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume,
            "predicted_price": prediction
        })

df_parsed.writeStream.foreachBatch(write_to_mongo).start().awaitTermination()

