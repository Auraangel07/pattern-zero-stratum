from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append('/opt/airflow')

from data_lake.ingestion.crypto import run_crypto_ingestion

default_args = {
    'owner': 'pattern_zero',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='stratum_crypto',
    default_args=default_args,
    schedule_interval='0 * * * *',
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=['stratum', 'crypto'],
) as dag:

    ingest_crypto = PythonOperator(
        task_id='ingest_crypto',
        python_callable=run_crypto_ingestion,
        op_kwargs={'period': '5d'},
    )