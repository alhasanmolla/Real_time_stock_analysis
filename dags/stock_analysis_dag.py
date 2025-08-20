from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.base import BaseSensorOperator
import socket
import subprocess
import os

BASE_DIR = os.path.abspath("A:/OneDrive/Desktop/Pyspark")

# ------------ PortSensor (ZooKeeper / Kafka availability) -------------
class PortSensor(BaseSensorOperator):
    def __init__(self, host, port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = port

    def poke(self, context):
        self.log.info(f"Checking {self.host}:{self.port} ...")
        try:
            with socket.create_connection((self.host, self.port), timeout=10):
                return True
        except Exception as e:
            self.log.error(f"Connection error: {e}")
            return False


# ------------ KafkaTopicSensor (Check topic existence) ----------------
class KafkaTopicSensor(BaseSensorOperator):
    def __init__(self, topic, kafka_path, bootstrap_server="localhost:9092", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.topic = topic
        self.bootstrap_server = bootstrap_server
        self.kafka_path = kafka_path  # path to Kafka bin/windows

    def poke(self, context):
        cmd = f'cd {self.kafka_path} && ./kafka-topics.bat --list --bootstrap-server {self.bootstrap_server}'
        self.log.info(f"Checking if topic '{self.topic}' exists...")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if self.topic in result.stdout.splitlines():
                self.log.info(f"Topic {self.topic} exists.")
                return True
            return False
        except Exception as e:
            self.log.error(f"Error while checking topic: {e}")
            return False


# ------------ Python helpers -----------------
def run_script(script_path):
    script_abs_path = os.path.join(BASE_DIR, script_path)
    result = subprocess.run(
        ["python", script_abs_path],
        check=True,
        text=True,
        capture_output=True
    )
    print(result.stdout)


# ------------ DAG Definition -----------------
with DAG(
    dag_id="stock_analysis_pipeline_with_topic_sensor",
    description="Stock pipeline using Kafka + Spark with topic sensor",
    start_date=datetime(2025, 8, 19),
    schedule=None,   # ✅ Airflow 3 uses `schedule`
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "airflow", "retries": 0},
    tags=["kafka", "spark", "stock"],
) as dag:

    # ------------ Sensors -----------------
    wait_for_zookeeper = PortSensor(
        task_id="wait_for_zookeeper",
        host="localhost",
        port=2181,
        poke_interval=10,
        timeout=180,
    )


    wait_for_kafka = PortSensor(
        task_id="wait_for_kafka",
        host="localhost",
        port=9092,
        poke_interval=10,
        timeout=180,
    )

    check_topic_exists = KafkaTopicSensor(
        task_id="check_topic_exists",
        topic="kap",
        kafka_path="A:/kafka/bin/windows",   # ⚠️ আপনার kafka bin path দিন
        bootstrap_server="localhost:9092",
        poke_interval=15,
        timeout=180,
    )

    # ------------ Pipeline tasks -----------------
    create_kafka_topic = BashOperator(
        task_id="create_kafka_topic",
        bash_command='cd A:/kafka && ./bin/windows/kafka-topics.bat --create --if-not-exists --topic kap --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1',
    )

    run_producer = PythonOperator(
        task_id='run_kafka_producer',
        python_callable=run_script,
        op_kwargs={'script_path': 'kafka_app/producer.py'},
    )

    train_model = PythonOperator(
        task_id='train_model',
        python_callable=run_script,
        op_kwargs={'script_path': 'spark_app/train_model.py'},
    )

    spark_streaming_command = BashOperator(
        task_id='spark_streaming_job',
        bash_command='A:/spark/bin/spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.6 streaming_job.py',
    )

    run_agent = PythonOperator(
        task_id='run_agent_streamlit',
        python_callable=run_script,
        op_kwargs={'script_path': 'mongodb_agent/agent_streamlit.py'},
    )

    run_dashboard = PythonOperator(
        task_id='run_dashboard',
        python_callable=run_script,
        op_kwargs={'script_path': 'streamlit_app/dashboard.py'},
    )

    # ------------ Dependencies -----------------
    wait_for_zookeeper >> wait_for_kafka >> create_kafka_topic >> check_topic_exists >> run_producer >> train_model >> spark_streaming_command >> run_agent >> run_dashboard
