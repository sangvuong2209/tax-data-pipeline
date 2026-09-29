SELECT 'co_quan_thue' AS bang, COUNT(*) AS so_dong FROM clean.co_quan_thue
UNION ALL SELECT 'dai_ly_thue', COUNT(*) FROM clean.dai_ly_thue
UNION ALL SELECT 'nhan_vien_dai_ly_thue', COUNT(*) FROM clean.nhan_vien_dai_ly_thue
UNION ALL SELECT 'nguoi_nop_thue', COUNT(*) FROM clean.nguoi_nop_thue;

-- Kiểm tra không còn trùng lặp
SELECT 'dai_ly_thue' AS bang, COUNT(*) - COUNT(DISTINCT ma_so_thue) AS con_trung FROM clean.dai_ly_thue
UNION ALL SELECT 'nguoi_nop_thue', COUNT(*) - COUNT(DISTINCT ma_so_thue) FROM clean.nguoi_nop_thue;
