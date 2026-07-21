from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append('/opt/airflow')

from data_lake.ingestion.news import run_news_ingestion

default_args = {
    'owner': 'pattern_zero',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='stratum_news',
    default_args=default_args,
    schedule_interval='0 6,22 * * *',
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=['stratum', 'news'],
) as dag:

    ingest_news = PythonOperator(
        task_id='ingest_news',
        python_callable=run_news_ingestion,
    )