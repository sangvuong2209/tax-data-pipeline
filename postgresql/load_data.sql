DROP TABLE IF EXISTS co_quan_thue;
DROP TABLE IF EXISTS dai_ly_thue;
DROP TABLE IF EXISTS nhan_vien_dai_ly_thue;
DROP TABLE IF EXISTS nguoi_nop_thue;

CREATE TABLE co_quan_thue (
    ma_co_quan_thue TEXT PRIMARY KEY,
    ten_co_quan_thue TEXT,
    dia_chi TEXT,
    co_quan_cap_tren TEXT,
    dia_ban_hoat_dong TEXT
);
\copy co_quan_thue FROM '/home/vm_sang/data-platform/data/raw/co_quan_thue.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TABLE dai_ly_thue (
    ma_so_thue TEXT,
    ten_dai_ly TEXT,
    dia_chi TEXT,
    co_quan_thue_quan_ly TEXT,
    nguoi_dai_dien_phap_luat TEXT,
    pham_vi_cung_cap_dich_vu TEXT,
    so_giay_xac_nhan TEXT,
    ngay_xac_nhan TEXT,
    tinh_trang_hoat_dong TEXT
);
\copy dai_ly_thue FROM '/home/vm_sang/data-platform/data/raw/dai_ly_thue.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TABLE nhan_vien_dai_ly_thue (
    ma_dinh_danh_ca_nhan TEXT,
    ho_va_ten TEXT,
    so_chung_chi_hanh_nghe TEXT,
    ngay_cap_chung_chi TEXT,
    co_quan_quan_ly_hanh_nghe TEXT,
    tinh_trang_hanh_nghe TEXT,
    ma_dai_ly_thue TEXT
);
\copy nhan_vien_dai_ly_thue FROM '/home/vm_sang/data-platform/data/raw/nhan_vien_dai_ly_thue.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TABLE nguoi_nop_thue (
    ma_so_thue TEXT,
    ten_nguoi_nop_thue TEXT,
    dia_chi TEXT,
    loai_nguoi_nop_thue TEXT,
    co_quan_thue_quan_ly TEXT,
    trang_thai_mst TEXT
);
\copy nguoi_nop_thue FROM '/home/vm_sang/data-platform/data/raw/nguoi_nop_thue.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

SELECT 'co_quan_thue' AS bang, COUNT(*) FROM co_quan_thue
UNION ALL SELECT 'dai_ly_thue', COUNT(*) FROM dai_ly_thue
UNION ALL SELECT 'nhan_vien_dai_ly_thue', COUNT(*) FROM nhan_vien_dai_ly_thue
UNION ALL SELECT 'nguoi_nop_thue', COUNT(*) FROM nguoi_nop_thue;
