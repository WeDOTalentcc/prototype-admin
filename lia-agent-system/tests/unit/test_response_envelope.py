"""UC-P1-11: ResponseEnvelope schema."""
from pydantic import BaseModel


def test_envelope_structure():
    from app.schemas.envelope import ResponseEnvelope
    r = ResponseEnvelope(data={"x": 1})
    d = r.model_dump()
    assert "data" in d
    assert "meta" in d
    assert "errors" in d


def test_envelope_with_typed_data():
    from app.schemas.envelope import ResponseEnvelope
    class UserOut(BaseModel):
        name: str
    r = ResponseEnvelope[UserOut](data=UserOut(name="test"))
    assert r.data.name == "test"


def test_envelope_errors_default_empty():
    from app.schemas.envelope import ResponseEnvelope
    r = ResponseEnvelope(data=None)
    assert r.errors == []


def test_envelope_request_id_optional():
    from app.schemas.envelope import ResponseEnvelope
    r = ResponseEnvelope(data={}, request_id="req-123")
    assert r.request_id == "req-123"


def test_error_envelope():
    from app.schemas.envelope import error_envelope
    r = error_envelope("Something failed", status_code=400)
    assert r.errors == ["Something failed"]
    assert r.data is None
