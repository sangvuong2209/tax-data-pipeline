from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.lineage.entities import Table

nguon_dan_cu = Table(
    cluster="national-population-postgres",
    database="national_population",
    name="public.dan_cu",
)

dich_dan_cu_dong_bo = Table(
    cluster="finance-sample-postgres",
    database="finance_sample",
    name="clean.dan_cu_dong_bo",
)

with DAG(
    dag_id="dong_bo_dan_cu",
    description="Đồng bộ tăng dần dữ liệu công dân từ CSDL Dân cư quốc gia về bản sao tham khảo phía BTC",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",  # 2h sáng mỗi ngày
    catchup=False,
    tags=["btc", "dan-cu", "sync"],
) as dag:

    chay_dong_bo = BashOperator(
        task_id="chay_script_dong_bo",
        bash_command="python3 /opt/airflow/sync-jobs/dong_bo_dan_cu.py",
        env={
            "BTC_DB_HOST": "192.168.100.131",
            "NATIONAL_API_HOST": "192.168.100.131",
        },
        append_env=True,
        inlets=[nguon_dan_cu],
        outlets=[dich_dan_cu_dong_bo],
    )
