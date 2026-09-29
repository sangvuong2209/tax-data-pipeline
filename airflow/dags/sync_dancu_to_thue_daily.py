from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.lineage.entities import Table

# --- 1. KHAI BÁO DATA LINEAGE CHO OPENMETADATA ---
nguon_dan_cu = Table(
    cluster="national-population-postgres",
    database="national_population",
    name="public.dan_cu",
)

dich_nguoi_nop_thue = Table(
    cluster="finance-sample-postgres",
    database="finance_sample",
    name="clean.nguoi_nop_thue", 
)

# --- 2. CẤU HÌNH KẾT NỐI (Dùng IP máy ảo) ---
SRC_DB = {
    "dbname": "national_population", 
    "user": "admin", 
    "password": "admin123456", 
    "host": "192.168.100.131", 
    "port": "5434"
}
API_URL = "http://192.168.100.131:8000/api/v1/sync/cong-dan/batch"

# --- 3. LOGIC XỬ LÝ (ETL) ---
def extract_and_load(**kwargs):
    # Kỹ thuật Local Import: Chỉ gọi thư viện khi task chạy để tránh crash Scheduler
    import psycopg2
    import psycopg2.extras
    import requests

    exec_date = kwargs.get('data_interval_start', datetime.now() - timedelta(days=1))
    
    conn = psycopg2.connect(**SRC_DB)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute(
        "SELECT so_dinh_danh, ho_ten, noi_thuong_tru FROM public.dan_cu"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("Không có biến động dữ liệu mới.")
        return

    payload = [
        {
            "ma_so_thue": r['so_dinh_danh'],
            "ten_nguoi_nop_thue": r['ho_ten'],
            "dia_chi": r['noi_thuong_tru'],
            "loai_nguoi_nop_thue": "Cá nhân",
            "co_quan_thue_quan_ly": "CCT_CG",
            "trang_thai_mst": "1"
        } for r in rows
    ]

    chunk_size = 1000
    for i in range(0, len(payload), chunk_size):
        batch = payload[i:i+chunk_size]
        resp = requests.post(API_URL, json=batch, timeout=30)
        resp.raise_for_status() 
        print(f"Đã đồng bộ lô {i//chunk_size + 1}: {len(batch)} bản ghi")

# --- 4. KHỞI TẠO DAG ---
with DAG(
    dag_id="sync_dancu_to_thue_daily",
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 0 * * *", 
    catchup=False,
    tags=["api-sync", "thue", "dan-cu"]
) as dag:

    sync_task = PythonOperator(
        task_id="call_api_to_sync_data",
        python_callable=extract_and_load,
        inlets=[nguon_dan_cu],
        outlets=[dich_nguoi_nop_thue],
        retries=3,
        retry_delay=timedelta(minutes=2)
    )