CREATE SCHEMA IF NOT EXISTS clean;

DROP TABLE IF EXISTS clean.co_quan_thue CASCADE;
DROP TABLE IF EXISTS clean.dai_ly_thue CASCADE;
DROP TABLE IF EXISTS clean.nhan_vien_dai_ly_thue CASCADE;
DROP TABLE IF EXISTS clean.nguoi_nop_thue CASCADE;

-- 1. co_quan_thue: đã sạch, chỉ copy + thêm PK
CREATE TABLE clean.co_quan_thue (
    ma_co_quan_thue TEXT PRIMARY KEY,
    ten_co_quan_thue TEXT,
    dia_chi TEXT,
    co_quan_cap_tren TEXT REFERENCES clean.co_quan_thue(ma_co_quan_thue),
    dia_ban_hoat_dong TEXT
);
INSERT INTO clean.co_quan_thue (ma_co_quan_thue, ten_co_quan_thue, dia_chi, dia_ban_hoat_dong)
SELECT ma_co_quan_thue, ten_co_quan_thue, dia_chi, dia_ban_hoat_dong FROM co_quan_thue
WHERE co_quan_cap_tren IS NULL OR co_quan_cap_tren = 'TCT' AND ma_co_quan_thue = 'TCT';
-- Chèn TCT trước (gốc cây), rồi mới chèn các dòng còn lại để tránh lỗi FK tự tham chiếu
INSERT INTO clean.co_quan_thue
SELECT ma_co_quan_thue, ten_co_quan_thue, dia_chi, NULLIF(co_quan_cap_tren, ''), dia_ban_hoat_dong
FROM co_quan_thue
WHERE ma_co_quan_thue NOT IN (SELECT ma_co_quan_thue FROM clean.co_quan_thue);

-- 2. dai_ly_thue: khử trùng theo ma_so_thue, null hóa FK sai
CREATE TABLE clean.dai_ly_thue (
    ma_so_thue TEXT PRIMARY KEY,
    ten_dai_ly TEXT,
    dia_chi TEXT,
    co_quan_thue_quan_ly TEXT REFERENCES clean.co_quan_thue(ma_co_quan_thue),
    nguoi_dai_dien_phap_luat TEXT,
    pham_vi_cung_cap_dich_vu TEXT,
    so_giay_xac_nhan TEXT,
    ngay_xac_nhan DATE,
    tinh_trang_hoat_dong TEXT
);
INSERT INTO clean.dai_ly_thue
SELECT DISTINCT ON (ma_so_thue)
    ma_so_thue,
    btrim(ten_dai_ly),
    btrim(dia_chi),
    NULLIF(co_quan_thue_quan_ly, '') FILTER (WHERE co_quan_thue_quan_ly IN (SELECT ma_co_quan_thue FROM clean.co_quan_thue)),
    nguoi_dai_dien_phap_luat,
    pham_vi_cung_cap_dich_vu,
    so_giay_xac_nhan,
    parse_flexible_date(ngay_xac_nhan),
    NULLIF(tinh_trang_hoat_dong, '')
FROM dai_ly_thue
WHERE ma_so_thue IS NOT NULL AND ma_so_thue <> ''
ORDER BY ma_so_thue, ctid;

-- 3. nhan_vien_dai_ly_thue: khử trùng theo ma_dinh_danh_ca_nhan, null hóa FK sai
CREATE TABLE clean.nhan_vien_dai_ly_thue (
    ma_dinh_danh_ca_nhan TEXT PRIMARY KEY,
    ho_va_ten TEXT,
    so_chung_chi_hanh_nghe TEXT,
    ngay_cap_chung_chi DATE,
    co_quan_quan_ly_hanh_nghe TEXT,
    tinh_trang_hanh_nghe TEXT,
    ma_dai_ly_thue TEXT REFERENCES clean.dai_ly_thue(ma_so_thue)
);
INSERT INTO clean.nhan_vien_dai_ly_thue
SELECT DISTINCT ON (ma_dinh_danh_ca_nhan)
    ma_dinh_danh_ca_nhan,
    btrim(ho_va_ten),
    so_chung_chi_hanh_nghe,
    parse_flexible_date(ngay_cap_chung_chi),
    co_quan_quan_ly_hanh_nghe,
    NULLIF(tinh_trang_hanh_nghe, ''),
    CASE WHEN ma_dai_ly_thue IN (SELECT ma_so_thue FROM clean.dai_ly_thue)
         THEN ma_dai_ly_thue ELSE NULL END
FROM nhan_vien_dai_ly_thue
WHERE ma_dinh_danh_ca_nhan IS NOT NULL AND length(ma_dinh_danh_ca_nhan) = 12
ORDER BY ma_dinh_danh_ca_nhan, ctid;

-- 4. nguoi_nop_thue: khử trùng theo ma_so_thue, null hóa FK sai
CREATE TABLE clean.nguoi_nop_thue (
    ma_so_thue TEXT PRIMARY KEY,
    ten_nguoi_nop_thue TEXT,
    dia_chi TEXT,
    loai_nguoi_nop_thue TEXT,
    co_quan_thue_quan_ly TEXT REFERENCES clean.co_quan_thue(ma_co_quan_thue),
    trang_thai_mst TEXT
);
INSERT INTO clean.nguoi_nop_thue
SELECT DISTINCT ON (ma_so_thue)
    ma_so_thue,
    btrim(ten_nguoi_nop_thue),
    btrim(dia_chi),
    NULLIF(loai_nguoi_nop_thue, ''),
    CASE WHEN co_quan_thue_quan_ly IN (SELECT ma_co_quan_thue FROM clean.co_quan_thue)
         THEN co_quan_thue_quan_ly ELSE NULL END,
    trang_thai_mst
FROM nguoi_nop_thue
WHERE ma_so_thue IS NOT NULL AND ma_so_thue <> ''
ORDER BY ma_so_thue, ctid;
