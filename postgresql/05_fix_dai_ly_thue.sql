TRUNCATE clean.dai_ly_thue;

INSERT INTO clean.dai_ly_thue
SELECT DISTINCT ON (ma_so_thue)
    ma_so_thue,
    btrim(ten_dai_ly),
    btrim(dia_chi),
    CASE WHEN co_quan_thue_quan_ly IN (SELECT ma_co_quan_thue FROM clean.co_quan_thue)
         THEN co_quan_thue_quan_ly ELSE NULL END,
    nguoi_dai_dien_phap_luat,
    pham_vi_cung_cap_dich_vu,
    so_giay_xac_nhan,
    parse_flexible_date(ngay_xac_nhan),
    NULLIF(tinh_trang_hoat_dong, '')
FROM dai_ly_thue
WHERE ma_so_thue IS NOT NULL AND ma_so_thue <> ''
ORDER BY ma_so_thue, ctid;

-- Chạy lại nhan_vien_dai_ly_thue vì trước đó dai_ly_thue còn rỗng, FK null 
TRUNCATE clean.nhan_vien_dai_ly_thue;

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
