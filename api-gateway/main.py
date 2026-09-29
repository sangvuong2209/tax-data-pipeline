from fastapi import FastAPI, HTTPException
import psycopg2
import psycopg2.extras

app = FastAPI(
    title="BTC Data Exchange API (mô phỏng)",
    description="API mô phỏng dịch vụ dữ liệu do BTC cung cấp qua trục tích hợp LGSP/NDXP",
    version="1.0.0",
)   

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "finance_sample",
    "user": "admin",
    "password": "admin123456",
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


@app.get("/api/v1/nguoi-nop-thue/{ma_so_thue}")
def get_nguoi_nop_thue(ma_so_thue: str):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM nguoi_nop_thue WHERE ma_so_thue = %s LIMIT 1;", (ma_so_thue,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy người nộp thuế")
    return row


@app.get("/api/v1/co-quan-thue/{ma_co_quan_thue}")
def get_co_quan_thue(ma_co_quan_thue: str):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM co_quan_thue WHERE ma_co_quan_thue = %s LIMIT 1;", (ma_co_quan_thue,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy cơ quan thuế")
    return row


@app.get("/health")
def health():
    return {"status": "ok"}
