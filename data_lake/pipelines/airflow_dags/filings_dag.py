from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append('/opt/airflow')

from data_lake.ingestion.filings import run_filings_ingestion

default_args = {
    'owner': 'pattern_zero',
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    dag_id='stratum_filings',
    default_args=default_args,
    schedule_interval='0 7 * * *',  # daily, 7am UTC
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=['stratum', 'filings'],
) as dag:

    ingest_filings = PythonOperator(
        task_id='ingest_filings',
        python_callable=run_filings_ingestion,
    )