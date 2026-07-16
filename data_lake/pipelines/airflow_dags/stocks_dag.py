from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append('/opt/airflow')

from data_lake.ingestion.stocks import run_stock_ingestion

default_args = {
    'owner': 'pattern_zero',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='stratum_stocks',
    default_args=default_args,
    schedule_interval='0 6,22 * * *',
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=['stratum', 'stocks'],
) as dag:

    ingest_stocks = PythonOperator(
        task_id='ingest_stocks',
        python_callable=run_stock_ingestion,
        op_kwargs={'period': '5d'},
    )