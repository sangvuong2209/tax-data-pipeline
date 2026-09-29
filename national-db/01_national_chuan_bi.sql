BEGIN;
DELETE FROM dan_cu a USING dan_cu b
WHERE a.so_dinh_danh = b.so_dinh_danh AND a.ctid > b.ctid;
UPDATE dan_cu SET ho_ten = btrim(ho_ten), noi_thuong_tru = btrim(noi_thuong_tru);
ALTER TABLE dan_cu ADD PRIMARY KEY (so_dinh_danh);
ALTER TABLE dan_cu ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE INDEX IF NOT EXISTS idx_dan_cu_updated_at ON dan_cu (updated_at);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_dan_cu_updated_at ON dan_cu;
CREATE TRIGGER trg_dan_cu_updated_at BEFORE UPDATE ON dan_cu
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMIT;

SELECT COUNT(*) AS so_cong_dan, COUNT(DISTINCT so_dinh_danh) AS so_id_duy_nhat FROM dan_cu;
