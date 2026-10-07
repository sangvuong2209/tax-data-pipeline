from fastapi import FastAPI, HTTPException
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(
    title="CSDL Quốc gia về Dân cư API (mô phỏng)",
    description="API mô phỏng dịch vụ tra cứu công dân do hệ thống Dân cư quốc gia cung cấp qua trục tích hợp NDXP",
    version="1.0.0",
)

DB_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "dbname": "national_population",
    "user": "admin",
    "password": "admin123456", 
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


@app.get("/api/v1/cong-dan/{so_dinh_danh}")
def get_cong_dan(so_dinh_danh: str):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM dan_cu WHERE so_dinh_danh = %s LIMIT 1;", (so_dinh_danh,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy công dân")
    return row


@app.get("/health")
def health():
    return {"status": "ok"}


class YeuCauDongBo(BaseModel):
    danh_sach: List[str]
    thay_doi_tu: Optional[datetime] = None


@app.post("/api/v1/cong-dan/dong-bo")
def dong_bo_cong_dan(yc: YeuCauDongBo):
    if not yc.danh_sach:
        raise HTTPException(status_code=422, detail="danh_sach không được rỗng")
    if len(yc.danh_sach) > 1000:
        raise HTTPException(status_code=422, detail="Tối đa 1000 số định danh mỗi lần gọi")

    tu = yc.thay_doi_tu or datetime(1970, 1, 1, tzinfo=timezone.utc)
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT now() AS bay_gio")
        thoi_diem_may_chu = cur.fetchone()["bay_gio"]

        cur.execute("SELECT so_dinh_danh FROM dan_cu WHERE so_dinh_danh = ANY(%s)", (yc.danh_sach,))
        ton_tai = {r["so_dinh_danh"] for r in cur.fetchall()}

        cur.execute(
            "SELECT so_dinh_danh, ho_ten, ngay_sinh, gioi_tinh, noi_thuong_tru, updated_at "
            "FROM dan_cu WHERE so_dinh_danh = ANY(%s) AND updated_at > %s ORDER BY so_dinh_danh",
            (yc.danh_sach, tu),
        )
        thay_doi = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    return {
        "thoi_diem_may_chu": thoi_diem_may_chu,
        "thay_doi": thay_doi,
        "khong_tim_thay": sorted(set(yc.danh_sach) - ton_tai),
    }