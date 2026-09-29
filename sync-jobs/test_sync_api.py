import psycopg2
import psycopg2.extras
import requests

# Cấu hình CSDL Dân cư (Nguồn)
SRC_DB = {
    "dbname": "national_population", 
    "user": "admin", 
    "password": "admin123456", 
    "host": "localhost", 
    "port": "5434"
}
API_URL = "http://localhost:8000/api/v1/sync/cong-dan/batch"

def run_test():
    print("1. Đang kết nối CSDL Dân cư...")
    try:
        conn = psycopg2.connect(**SRC_DB)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT so_dinh_danh, ho_ten, noi_thuong_tru FROM public.dan_cu LIMIT 10")
        rows = cur.fetchall()
        cur.close(); conn.close()
    except Exception as e:
        print(f"Lỗi kết nối Database Nguồn: {e}")
        return

    if not rows:
        print("Không có dữ liệu để test.")
        return

    print(f"2. Đã lấy {len(rows)} dòng. Đang chuyển đổi định dạng...")
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

    print("3. Đang gọi API Thuế...")
    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"THÀNH CÔNG: {resp.json()}")
        else:
            print(f"API LỖI ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"Lỗi gọi API: {e}")

if __name__ == '__main__':
    run_test()