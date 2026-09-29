-- Đếm trùng lặp
SELECT 'dai_ly_thue - dòng trùng ma_so_thue' AS kiem_tra,
       COUNT(*) - COUNT(DISTINCT ma_so_thue) AS so_dong_loi FROM dai_ly_thue
UNION ALL
SELECT 'nguoi_nop_thue - dòng trùng ma_so_thue',
       COUNT(*) - COUNT(DISTINCT ma_so_thue) FROM nguoi_nop_thue
UNION ALL
SELECT 'nhan_vien_dai_ly_thue - dòng trùng ma_dinh_danh_ca_nhan',
       COUNT(*) - COUNT(DISTINCT ma_dinh_danh_ca_nhan) FROM nhan_vien_dai_ly_thue;

-- Đếm "mồ côi" (orphan) - giá trị FK không khớp bảng cha
SELECT 'dai_ly_thue - co_quan_thue_quan_ly không hợp lệ' AS kiem_tra,
       COUNT(*) FILTER (WHERE co_quan_thue_quan_ly IS NULL OR co_quan_thue_quan_ly = ''
                         OR co_quan_thue_quan_ly NOT IN (SELECT ma_co_quan_thue FROM co_quan_thue)) AS so_dong_loi
FROM dai_ly_thue
UNION ALL
SELECT 'nguoi_nop_thue - co_quan_thue_quan_ly không hợp lệ',
       COUNT(*) FILTER (WHERE co_quan_thue_quan_ly IS NULL OR co_quan_thue_quan_ly = ''
                         OR co_quan_thue_quan_ly NOT IN (SELECT ma_co_quan_thue FROM co_quan_thue))
FROM nguoi_nop_thue
UNION ALL
SELECT 'nhan_vien_dai_ly_thue - ma_dai_ly_thue không hợp lệ',
       COUNT(*) FILTER (WHERE ma_dai_ly_thue IS NULL OR ma_dai_ly_thue = ''
                         OR ma_dai_ly_thue NOT IN (SELECT ma_so_thue FROM dai_ly_thue))
FROM nhan_vien_dai_ly_thue;
