CREATE OR REPLACE FUNCTION parse_flexible_date(txt TEXT) RETURNS DATE AS $$
DECLARE
    result DATE;
BEGIN
    IF txt IS NULL OR btrim(txt) = '' THEN
        RETURN NULL;
    END IF;
    BEGIN
        result := to_date(btrim(txt), 'DD/MM/YYYY');
        IF to_char(result, 'DD/MM/YYYY') = btrim(txt) THEN RETURN result; END IF;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
    BEGIN
        result := to_date(btrim(txt), 'YYYY-MM-DD');
        IF to_char(result, 'YYYY-MM-DD') = btrim(txt) THEN RETURN result; END IF;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
    BEGIN
        result := to_date(btrim(txt), 'DD-MM-YYYY');
        IF to_char(result, 'DD-MM-YYYY') = btrim(txt) THEN RETURN result; END IF;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
    RETURN NULL;  -- không khớp định dạng nào, hoặc ngày không hợp lệ (vd 31/02) -> NULL
END;
$$ LANGUAGE plpgsql;
