"""
Sensor: voice_collection_script — funções puras da coleta por voz (Fase 4 fundação).
"""
from app.domains.communication.services.voice_collection_script import (
    build_collection_script,
    is_sensitive_field,
    is_voice_collectable,
    normalize_field_value,
    portal_only_fields,
)


def test_voice_collectable_excludes_file_and_photo():
    assert is_voice_collectable("text") is True
    assert is_voice_collectable("cpf") is True
    assert is_voice_collectable("file") is False
    assert is_voice_collectable("photo") is False


def test_sensitive_by_type_and_by_name():
    assert is_sensitive_field("cpf", "cpf") is True          # tipo
    assert is_sensitive_field("dados_bancarios", "text") is True  # nome (banco)
    assert is_sensitive_field("pis", "text") is True
    assert is_sensitive_field("rg", "text") is True
    assert is_sensitive_field("full_name", "text") is False  # comum


def test_build_script_skips_completed_and_flags():
    fields = [
        {"name": "full_name", "label": "Nome", "field_type": "text", "is_required": True},
        {"name": "cpf", "label": "CPF", "field_type": "cpf", "is_required": True},
        {"name": "cv_document", "label": "Currículo", "field_type": "file", "is_required": False},
        {"name": "bank", "label": "Dados Bancários", "field_type": "text", "is_required": True},
    ]
    script = build_collection_script(fields, completed_names=["full_name"])
    names = [p.name for p in script]
    assert names == ["cpf", "cv_document", "bank"]  # full_name pulado, ordem preservada
    by = {p.name: p for p in script}
    assert by["cpf"].sensitive is True
    assert by["cv_document"].voice_collectable is False
    assert by["bank"].sensitive is True
    assert by["full_name" if False else "cpf"].voice_collectable is True


def test_portal_only_fields():
    fields = [
        {"name": "cpf", "field_type": "cpf"},
        {"name": "cv", "field_type": "file"},
        {"name": "rg_scan", "field_type": "photo"},
    ]
    script = build_collection_script(fields)
    portal = [p.name for p in portal_only_fields(script)]
    assert portal == ["cv", "rg_scan"]


def test_build_script_accepts_enum_like_type():
    class _Enum:
        value = "CPF"
    script = build_collection_script([{"name": "cpf", "field_type": _Enum()}])
    assert script[0].field_type == "cpf"
    assert script[0].sensitive is True


def test_normalize_cpf_from_digits_and_words():
    # dígitos diretos
    r = normalize_field_value("cpf", "123.456.789-09")
    assert r.value == "12345678909" and r.valid is True
    # ditado por palavras
    r2 = normalize_field_value("cpf", "um dois tres quatro cinco seis sete oito nove zero um")
    assert r2.value == "12345678901" and r2.valid is True
    # tamanho errado
    r3 = normalize_field_value("cpf", "123")
    assert r3.valid is False and r3.error == "cpf_invalid_length"


def test_normalize_phone_and_number():
    assert normalize_field_value("phone", "(11) 98888-7777").value == "11988887777"
    assert normalize_field_value("phone", "(11) 98888-7777").valid is True
    assert normalize_field_value("phone", "123").valid is False
    assert normalize_field_value("number", "abc 42").value == "42"


def test_normalize_email_spoken():
    r = normalize_field_value("email", "maria arroba empresa ponto com")
    assert r.value == "maria@empresa.com" and r.valid is True
    assert normalize_field_value("email", "sem arroba aqui").valid is False


def test_normalize_text_passthrough_and_empty():
    assert normalize_field_value("text", "  Rua das Flores 10 ").value == "Rua das Flores 10"
    assert normalize_field_value("address", "Av Paulista").valid is True
    e = normalize_field_value("text", "   ")
    assert e.valid is False and e.error == "empty"


def test_normalize_date_passthrough_to_llm():
    r = normalize_field_value("date", "primeiro de janeiro de 1990")
    assert r.valid is True and r.value == "primeiro de janeiro de 1990"
