from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append('/opt/airflow')

from data_lake.ingestion.macro import run_macro_ingestion

default_args = {
    'owner': 'pattern_zero',
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
}

with DAG(
    dag_id='stratum_macro',
    default_args=default_args,
    schedule_interval='0 8 * * 1',
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=['stratum', 'macro'],
) as dag:

    ingest_macro = PythonOperator(
        task_id='ingest_macro',
        python_callable=run_macro_ingestion,
    )