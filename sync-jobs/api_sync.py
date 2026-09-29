from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
import psycopg2
from psycopg2.extras import execute_values

app = FastAPI(title="API Tiếp nhận Dữ liệu Dân cư - Ngành Thuế")

DB_CONFIG = {
    "dbname": "finance_sample",
    "user": "admin",
    "password": "admin123456", 
    "host": "192.168.100.131",
    "port": "5433"
}

# Payload chung dùng cho cả 2 API
class NguoiNopThuePayload(BaseModel):
    ma_so_thue: str
    ten_nguoi_nop_thue: str
    dia_chi: str
    loai_nguoi_nop_thue: str = "Cá nhân" 
    co_quan_thue_quan_ly: str = None
    trang_thai_mst: str = None

    @validator('ma_so_thue', 'ten_nguoi_nop_thue', 'dia_chi', pre=True)
    def trim_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

# ==========================================
# 1. API ĐỒNG BỘ ĐƠN LẺ (SINGLE) - REALTIME
# ==========================================
@app.post("/api/v1/sync/cong-dan")
def sync_nguoi_nop_thue_single(data: NguoiNopThuePayload):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = """
            INSERT INTO clean.nguoi_nop_thue (
                ma_so_thue, ten_nguoi_nop_thue, dia_chi, 
                loai_nguoi_nop_thue, co_quan_thue_quan_ly, trang_thai_mst
            )
            VALUES (
                %(mst)s, %(ten)s, %(dia_chi)s, %(loai)s, 
                (SELECT ma_co_quan_thue FROM clean.co_quan_thue WHERE ma_co_quan_thue = %(cqt)s), 
                %(trang_thai)s
            )
            ON CONFLICT (ma_so_thue) 
            DO UPDATE SET 
                ten_nguoi_nop_thue = EXCLUDED.ten_nguoi_nop_thue,
                dia_chi = EXCLUDED.dia_chi,
                loai_nguoi_nop_thue = EXCLUDED.loai_nguoi_nop_thue,
                co_quan_thue_quan_ly = EXCLUDED.co_quan_thue_quan_ly,
                trang_thai_mst = EXCLUDED.trang_thai_mst;
        """
        
        payload_dict = {
            "mst": data.ma_so_thue,
            "ten": data.ten_nguoi_nop_thue,
            "dia_chi": data.dia_chi,
            "loai": data.loai_nguoi_nop_thue,
            "cqt": data.co_quan_thue_quan_ly,
            "trang_thai": data.trang_thai_mst
        }
        
        cur.execute(query, payload_dict)
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success", "message": f"Đã đồng bộ công dân: {data.ten_nguoi_nop_thue}"}
    
    except Exception as e:
        if 'conn' in locals(): conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 2. API ĐỒNG BỘ HÀNG LOẠT (BATCH) - ĐỊNH KỲ
# ==========================================
@app.post("/api/v1/sync/cong-dan/batch")
def sync_nguoi_nop_thue_batch(data_list: List[NguoiNopThuePayload]):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # --- BƯỚC KHỬ TRÙNG LẶP THEO MA_SO_THUE TRONG LÔ ---
        seen = set()
        unique_data_list = []
        for item in data_list:
            if item.ma_so_thue not in seen:
                seen.add(item.ma_so_thue)
                unique_data_list.append(item)
        # ---------------------------------------------------

        query = """
            INSERT INTO clean.nguoi_nop_thue (
                ma_so_thue, ten_nguoi_nop_thue, dia_chi, 
                loai_nguoi_nop_thue, co_quan_thue_quan_ly, trang_thai_mst
            )
            VALUES %s
            ON CONFLICT (ma_so_thue) 
            DO UPDATE SET 
                ten_nguoi_nop_thue = EXCLUDED.ten_nguoi_nop_thue,
                dia_chi = EXCLUDED.dia_chi,
                loai_nguoi_nop_thue = EXCLUDED.loai_nguoi_nop_thue,
                co_quan_thue_quan_ly = EXCLUDED.co_quan_thue_quan_ly,
                trang_thai_mst = EXCLUDED.trang_thai_mst;
        """
        
        values_to_insert = [
            (
                item.ma_so_thue, 
                item.ten_nguoi_nop_thue, 
                item.dia_chi, 
                item.loai_nguoi_nop_thue, 
                item.co_quan_thue_quan_ly, 
                item.trang_thai_mst
            ) for item in unique_data_list
        ]
        
        sql_template = "(%s, %s, %s, %s, (SELECT ma_co_quan_thue FROM clean.co_quan_thue WHERE ma_co_quan_thue = %s), %s)"
        
        execute_values(cur, query, values_to_insert, template=sql_template, page_size=1000)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "status": "success", 
            "message": f"Đã đồng bộ thành công lô {len(unique_data_list)} bản ghi NNT (Đã lọc bỏ trùng lặp)."
        }
    
    except Exception as e:
        print("--- LỖI THỰC TẾ TỪ DB ---:", str(e))
        if 'conn' in locals(): conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))