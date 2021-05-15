from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from datetime import datetime

with DAG(
    dag_id="example_dag",
    default_args={"start_date": datetime(2020, 5, 1), "owner": "airflow"},
    schedule_interval=None,
) as dag:

    bash_task = BashOperator(
        task_id="sample_bash_operator",
        bash_command="echo Test",
    )

    bq_task = BigQueryOperator(
        task_id="sample_bq_operator",
        sql="SELECT * FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips` LIMIT 1000",
        use_legacy_sql=False,
        location="asia-northeast1"
    )

    bash_task >> bq_task
