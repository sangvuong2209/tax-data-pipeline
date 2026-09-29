CREATE TABLE IF NOT EXISTS clean.dong_bo_trang_thai (
    ten_job      TEXT PRIMARY KEY,
    moc_dong_bo  TIMESTAMPTZ NOT NULL,
    cap_nhat_luc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clean.dong_bo_nnt_log (
    id           BIGSERIAL PRIMARY KEY,
    run_id       TEXT NOT NULL,
    ma_so_thue   TEXT NOT NULL,
    truong       TEXT NOT NULL,
    gia_tri_cu   TEXT,
    gia_tri_moi  TEXT,
    ghi_nhan_luc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dong_bo_nnt_log_run ON clean.dong_bo_nnt_log (run_id);

CREATE TABLE IF NOT EXISTS clean.dong_bo_nnt_khong_tim_thay (
    ma_so_thue    TEXT PRIMARY KEY REFERENCES clean.nguoi_nop_thue(ma_so_thue),
    phat_hien_luc TIMESTAMPTZ NOT NULL DEFAULT now()
);
