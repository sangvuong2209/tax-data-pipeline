SELECT 'co_quan_thue' AS bang, COUNT(*) AS so_dong FROM clean.co_quan_thue
UNION ALL SELECT 'dai_ly_thue', COUNT(*) FROM clean.dai_ly_thue
UNION ALL SELECT 'nhan_vien_dai_ly_thue', COUNT(*) FROM clean.nhan_vien_dai_ly_thue
UNION ALL SELECT 'nguoi_nop_thue', COUNT(*) FROM clean.nguoi_nop_thue;

-- Kiểm tra tỉ lệ nhân viên có gắn đúng đại lý (không còn null hết)
SELECT COUNT(*) AS tong,
       COUNT(ma_dai_ly_thue) AS co_gan_dai_ly,
       ROUND(100.0 * COUNT(ma_dai_ly_thue) / COUNT(*), 1) AS ty_le_phan_tram
FROM clean.nhan_vien_dai_ly_thue;
