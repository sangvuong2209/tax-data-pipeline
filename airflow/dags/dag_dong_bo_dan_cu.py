from datetime import datetime, timezone
from airflow import DAG
from airflow.operators.python import PythonOperator
import psycopg2
import requests
import uuid

# Cấu hình kết nối và tham số mặc định của DAG
default_args = {
    'owner': 'data_engineer_sang',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
}

BTC_DB_CONFIG = {
    "host": "localhost", "port": 5432, "dbname": "finance_sample",
    "user": "admin", "password": "admin123456",
}
NATIONAL_API_DONG_BO_URL = "http://localhost:8001/api/v1/cong-dan/dong-bo"
TEN_JOB = "dong_bo_dan_cu"
KICH_THUOC_LO = 500

def task_dam_bao_bang_dich():
    """Đảm bảo bảng đích clean.dan_cu_dong_bo tồn tại trước khi đồng bộ."""
    conn = psycopg2.connect(**BTC_DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clean.dan_cu_dong_bo (
                so_dinh_danh TEXT PRIMARY KEY,
                ho_ten TEXT,
                ngay_sinh TEXT,
                gioi_tinh TEXT,
                noi_thuong_tru TEXT,
                nguon_cap_nhat_luc TIMESTAMPTZ,
                dong_bo_luc TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
    conn.commit()
    conn.close()

def task_thuc_hien_dong_bo(**context):
    """Thực hiện logic kéo dữ liệu thay đổi tăng dần (incremental sync) qua API."""
    run_id = context['run_id']
    print(f"[run_id={run_id}] Bắt đầu tiến trình đồng bộ tự động qua Airflow...")

    conn = psycopg2.connect(**BTC_DB_CONFIG)
    
    # 1. Lấy mốc đồng bộ lần trước từ bảng trạng thái
    with conn.cursor() as cur:
        cur.execute(
            "SELECT moc_dong_bo FROM clean.dong_bo_trang_thai WHERE ten_job = %s",
            (TEN_JOB,),
        )
        row = cur.fetchone()
    moc_truoc = row[0] if row else datetime(1970, 1, 1, tzinfo=timezone.utc)

    # 2. Lấy danh sách mã số thuế cá nhân cần theo dõi
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ma_so_thue FROM clean.nguoi_nop_thue WHERE loai_nguoi_nop_thue = 'Cá nhân'"
        )
        danh_sach_mst = [r[0] for r in cur.fetchall()]

    tong_thay_doi = 0
    moc_moi = moc_truoc

    with conn.cursor() as cur:
        # Chia nhỏ danh sách thành từng lô (batch) để gọi API
        for i in range(0, len(danh_sach_mst), KICH_THUOC_LO):
            lo = danh_sach_mst[i:i + KICH_THUOC_LO]
            resp = requests.post(
                NATIONAL_API_DONG_BO_URL,
                json={"danh_sach": lo, "thay_doi_tu": moc_truoc.isoformat()},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            moc_may_chu = datetime.fromisoformat(data["thoi_diem_may_chu"])
            if moc_may_chu > moc_moi:
                moc_moi = moc_may_chu

            # Xử lý từng bản ghi thay đổi trả về từ API
            for ban_ghi in data["thay_doi"]:
                so_dinh_danh = ban_ghi["so_dinh_danh"]
                ban_ghi["updated_at"] = datetime.fromisoformat(ban_ghi["updated_at"])
                
                # Kiểm tra dữ liệu cũ để ghi log thay đổi (Auditing)
                cur.execute(
                    "SELECT ho_ten, ngay_sinh, gioi_tinh, noi_thuong_tru FROM clean.dan_cu_dong_bo WHERE so_dinh_danh = %s",
                    (so_dinh_danh,),
                )
                hien_co = cur.fetchone()

                if hien_co:
                    cu = {"ho_ten": hien_co[0], "ngay_sinh": hien_co[1], "gioi_tinh": hien_co[2], "noi_thuong_tru": hien_co[3]}
                    for truong in ("ho_ten", "ngay_sinh", "gioi_tinh", "noi_thuong_tru"):
                        if cu[truong] != ban_ghi.get(truong):
                            cur.execute(
                                "INSERT INTO clean.dong_bo_nnt_log (run_id, ma_so_thue, truong, gia_tri_cu, gia_tri_moi) "
                                "VALUES (%s, %s, %s, %s, %s)",
                                (run_id, so_dinh_danh, truong, cu[truong], ban_ghi.get(truong)),
                            )
                
                # Thực hiện lệnh UPSERT vào bảng đích
                cur.execute(
                    """
                    INSERT INTO clean.dan_cu_dong_bo (so_dinh_danh, ho_ten, ngay_sinh, gioi_tinh, noi_thuong_tru, nguon_cap_nhat_luc, dong_bo_luc)
                    VALUES (%(so_dinh_danh)s, %(ho_ten)s, %(ngay_sinh)s, %(gioi_tinh)s, %(noi_thuong_tru)s, %(updated_at)s, now())
                    ON CONFLICT (so_dinh_danh) DO UPDATE SET
                        ho_ten = EXCLUDED.ho_ten,
                        ngay_sinh = EXCLUDED.ngay_sinh,
                        gioi_tinh = EXCLUDED.gioi_tinh,
                        noi_thuong_tru = EXCLUDED.noi_thuong_tru,
                        nguon_cap_nhat_luc = EXCLUDED.nguon_cap_nhat_luc,
                        dong_bo_luc = now();
                    """,
                    ban_ghi,
                )
                tong_thay_doi += 1

            # Lưu danh sách không tìm thấy để rà soát[cite: 3]
            for mst in data["khong_tim_thay"]:
                cur.execute(
                    "INSERT INTO clean.dong_bo_nnt_khong_tim_thay (ma_so_thue) VALUES (%s) "
                    "ON CONFLICT (ma_so_thue) DO NOTHING",
                    (mst,),
                )

        # Cập nhật mốc thời điểm đồng bộ mới cho lần chạy kế tiếp[cite: 3]
        cur.execute(
            "INSERT INTO clean.dong_bo_trang_thai (ten_job, moc_dong_bo) VALUES (%s, %s) "
            "ON CONFLICT (ten_job) DO UPDATE SET moc_dong_bo = EXCLUDED.moc_dong_bo, cap_nhat_luc = now()",
            (TEN_JOB, moc_moi),
        )

    conn.commit()
    conn.close()
    print(f"Hoàn tất đồng bộ. Tổng số bản ghi thay đổi: {tong_thay_doi}")

# Định nghĩa DAG chạy tự động mỗi ngày vào lúc 1 giờ sáng
with DAG(
    dag_id='etl_dong_bo_dan_cu_to_btc',
    default_args=default_args,
    description='Pipeline tự động đồng bộ dữ liệu dân cư sang hệ thống Thuế qua API',
    schedule_interval='0 1 * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['etl', 'tax', 'population', 'sync'],
) as dag:

    t1 = PythonOperator(
        task_id='dam_bao_bang_dich_task',
        python_callable=task_dam_bao_bang_dich,
    )

    t2 = PythonOperator(
        task_id='thuc_hien_dong_bo_task',
        python_callable=task_thuc_hien_dong_bo,
    )

    # Trình tự thực hiện: Chuẩn hóa bảng đích trước -> Chạy luồng đồng bộ API sau
    t1 >> t2