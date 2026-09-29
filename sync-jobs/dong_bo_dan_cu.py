"""
Đồng bộ dữ liệu công dân từ CSDL Dân cư quốc gia về BTC.

Khác với script đối chiếu (sync_nnt_dan_cu.py) chỉ SO SÁNH rồi in kết quả,
script này THỰC SỰ GHI dữ liệu: kéo phần thay đổi từ CSDL Dân cư (qua API,
không kết nối DB trực tiếp) và cập nhật vào bảng chỉ-đọc phía BTC
(clean.dan_cu_dong_bo). BTC không ghi ngược lại CSDL Dân cư -> không vi phạm
quyền sở hữu dữ liệu của hệ thống nguồn.

Đồng bộ theo kiểu tăng dần (incremental): mỗi lần chạy chỉ lấy các bản ghi
có updated_at mới hơn mốc lần chạy trước (lưu trong clean.dong_bo_trang_thai).
Mọi thay đổi được ghi vào clean.dong_bo_nnt_log để truy vết.
"""

import sys
import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import requests

BTC_DB_CONFIG = {
    "host": "localhost", "port": 5433, "dbname": "finance_sample",
    "user": "admin", "password": "admin123456",
}
NATIONAL_API_DONG_BO_URL = "http://localhost:8001/api/v1/cong-dan/dong-bo"
TEN_JOB = "dong_bo_dan_cu"
KICH_THUOC_LO = 500  # số định danh gửi mỗi lần gọi API


def lay_moc_dong_bo_truoc(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT moc_dong_bo FROM clean.dong_bo_trang_thai WHERE ten_job = %s",
            (TEN_JOB,),
        )
        row = cur.fetchone()
    return row[0] if row else datetime(1970, 1, 1, tzinfo=timezone.utc)


def lay_danh_sach_ca_nhan(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ma_so_thue FROM clean.nguoi_nop_thue WHERE loai_nguoi_nop_thue = 'Cá nhân'"
        )
        return [r[0] for r in cur.fetchall()]


def chia_lo(danh_sach, kich_thuoc):
    for i in range(0, len(danh_sach), kich_thuoc):
        yield danh_sach[i:i + kich_thuoc]


def dam_bao_bang_dich(conn):
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


def ghi_log(cur, run_id, ma_so_thue, truong, gia_tri_cu, gia_tri_moi):
    if gia_tri_cu == gia_tri_moi:
        return
    cur.execute(
        "INSERT INTO clean.dong_bo_nnt_log (run_id, ma_so_thue, truong, gia_tri_cu, gia_tri_moi) "
        "VALUES (%s, %s, %s, %s, %s)",
        (run_id, ma_so_thue, truong, gia_tri_cu, gia_tri_moi),
    )


def upsert_ban_ghi(cur, run_id, ban_ghi):
    so_dinh_danh = ban_ghi["so_dinh_danh"]
    cur.execute(
        "SELECT ho_ten, ngay_sinh, gioi_tinh, noi_thuong_tru FROM clean.dan_cu_dong_bo WHERE so_dinh_danh = %s",
        (so_dinh_danh,),
    )
    hien_co = cur.fetchone()

    if hien_co:
        cu = {"ho_ten": hien_co[0], "ngay_sinh": hien_co[1], "gioi_tinh": hien_co[2], "noi_thuong_tru": hien_co[3]}
        for truong in ("ho_ten", "ngay_sinh", "gioi_tinh", "noi_thuong_tru"):
            ghi_log(cur, run_id, so_dinh_danh, truong, cu[truong], ban_ghi.get(truong))
    else:
        ghi_log(cur, run_id, so_dinh_danh, "(bản ghi mới)", None, ban_ghi.get("ho_ten"))

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


def main():
    run_id = str(uuid.uuid4())
    print(f"[run_id={run_id}] Bắt đầu đồng bộ...")

    conn = psycopg2.connect(**BTC_DB_CONFIG)
    dam_bao_bang_dich(conn)

    moc_truoc = lay_moc_dong_bo_truoc(conn)
    print(f"Mốc đồng bộ lần trước: {moc_truoc.isoformat()}")

    danh_sach_mst = lay_danh_sach_ca_nhan(conn)
    print(f"Số người nộp thuế Cá nhân cần theo dõi: {len(danh_sach_mst):,}")

    tong_thay_doi = 0
    tong_khong_tim_thay = 0
    moc_moi = moc_truoc

    with conn.cursor() as cur:
        for lo in chia_lo(danh_sach_mst, KICH_THUOC_LO):
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

            for ban_ghi in data["thay_doi"]:
                ban_ghi["updated_at"] = datetime.fromisoformat(ban_ghi["updated_at"])
                upsert_ban_ghi(cur, run_id, ban_ghi)
                tong_thay_doi += 1

            for mst in data["khong_tim_thay"]:
                cur.execute(
                    "INSERT INTO clean.dong_bo_nnt_khong_tim_thay (ma_so_thue) VALUES (%s) "
                    "ON CONFLICT (ma_so_thue) DO NOTHING",
                    (mst,),
                )
            tong_khong_tim_thay += len(data["khong_tim_thay"])

        cur.execute(
            "INSERT INTO clean.dong_bo_trang_thai (ten_job, moc_dong_bo) VALUES (%s, %s) "
            "ON CONFLICT (ten_job) DO UPDATE SET moc_dong_bo = EXCLUDED.moc_dong_bo, cap_nhat_luc = now()",
            (TEN_JOB, moc_moi),
        )

    conn.commit()
    conn.close()

    print(f"\n--- Kết quả ---")
    print(f"Bản ghi được đồng bộ (thêm mới/cập nhật): {tong_thay_doi:,}")
    print(f"Không tìm thấy trong CSDL Dân cư (lũy kế, có trùng lặp giữa các lô): {tong_khong_tim_thay:,}")
    print(f"Mốc đồng bộ mới: {moc_moi.isoformat()}")


if __name__ == "__main__":
    main()