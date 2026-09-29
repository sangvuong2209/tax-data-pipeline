DROP TABLE IF EXISTS dan_cu;

CREATE TABLE dan_cu (
    so_dinh_danh TEXT,
    ho_ten TEXT,
    ngay_sinh TEXT,
    gioi_tinh TEXT,
    noi_thuong_tru TEXT
);
\copy dan_cu FROM '/home/vm_sang/data-platform/data/raw/csdl_quoc_gia_dan_cu.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

SELECT COUNT(*) FROM dan_cu;
