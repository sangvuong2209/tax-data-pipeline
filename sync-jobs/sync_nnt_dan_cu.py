"""
Script đồng bộ/đối chiếu: BTC gọi sang API CSDL Quốc gia (Dân cư)
để xác minh thông tin người nộp thuế loại Cá nhân.

Nguyên tắc: BTC KHÔNG kết nối trực tiếp vào DB national_population,
chỉ gọi qua API công khai (mô phỏng trục tích hợp LGSP/NDXP).
"""

import psycopg2
import psycopg2.extras
import requests

BTC_DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "finance_sample",
    "user": "admin",
    "password": "admin123456",
}

NATIONAL_API_URL = "http://localhost:8001/api/v1/cong-dan"


def get_ca_nhan_nnt(limit=20):
    """Lấy danh sách người nộp thuế loại Cá nhân từ BTC."""
    conn = psycopg2.connect(**BTC_DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT ma_so_thue, ten_nguoi_nop_thue FROM nguoi_nop_thue "
        "WHERE loai_nguoi_nop_thue = 'Cá nhân' LIMIT %s;",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def doi_chieu(ma_so_thue, ten_khai_thue):
    """Gọi API Dân cư quốc gia, đối chiếu tên đã khai thuế với tên trong CSDL dân cư."""
    try:
        resp = requests.get(f"{NATIONAL_API_URL}/{ma_so_thue}", timeout=5)
    except requests.exceptions.RequestException as e:
        return {"ma_so_thue": ma_so_thue, "ket_qua": "LỖI KẾT NỐI", "chi_tiet": str(e)}

    if resp.status_code == 404:
        return {"ma_so_thue": ma_so_thue, "ket_qua": "KHÔNG TÌM THẤY trong CSDL Dân cư"}

    if resp.status_code != 200:
        return {"ma_so_thue": ma_so_thue, "ket_qua": f"LỖI API ({resp.status_code})"}

    data = resp.json()
    ten_dan_cu = data.get("ho_ten", "").strip().upper()
    ten_thue = ten_khai_thue.strip().upper()

    khop = ten_dan_cu == ten_thue
    return {
        "ma_so_thue": ma_so_thue,
        "ten_khai_thue": ten_khai_thue,
        "ten_dan_cu": data.get("ho_ten"),
        "ket_qua": "KHỚP" if khop else "SAI LỆCH",
    }


def main():
    print("Lấy danh sách người nộp thuế Cá nhân từ BTC...")
    danh_sach = get_ca_nhan_nnt(limit=20)
    print(f"-> Lấy được {len(danh_sach)} người nộp thuế để đối chiếu\n")

    ket_qua_tong_hop = {"KHỚP": 0, "SAI LỆCH": 0, "KHÔNG TÌM THẤY trong CSDL Dân cư": 0}

    for nnt in danh_sach:
        kq = doi_chieu(nnt["ma_so_thue"], nnt["ten_nguoi_nop_thue"])
        print(kq)
        key = kq.get("ket_qua", "")
        if key in ket_qua_tong_hop:
            ket_qua_tong_hop[key] += 1
        elif "LỖI" in key:
            ket_qua_tong_hop.setdefault(key, 0)
            ket_qua_tong_hop[key] += 1

    print("\n--- Tổng hợp ---")
    for k, v in ket_qua_tong_hop.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
