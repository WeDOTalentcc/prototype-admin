import re
from app.api.v1._path_patterns import SESSION_ID_PATH_PATTERN, DUAL_ID_PATH_PATTERN

def test_accepts_lia_session_format():
    assert re.match(SESSION_ID_PATH_PATTERN, "lia-1780000000000-zoeova")

def test_accepts_uuid_and_bigint():
    assert re.match(SESSION_ID_PATH_PATTERN, "12345678-1234-1234-1234-123456789012")
    assert re.match(SESSION_ID_PATH_PATTERN, "4827")

def test_rejects_path_traversal():
    assert not re.match(SESSION_ID_PATH_PATTERN, "../secret")
    assert not re.match(SESSION_ID_PATH_PATTERN, "a/b/c")

def test_old_dual_id_pattern_rejected_lia_format_regression_doc():
    # Documenta o bug que isto corrige: o padrão antigo (UUID/bigint) rejeitava lia-*.
    assert not re.match(DUAL_ID_PATH_PATTERN, "lia-1780000000000-zoeova")
