"""
Testes unitários para a política de lifecycle de audit logs S3.

Cobertura:
- get_lifecycle_config() retorna estrutura válida com "Rules"
- Dias de retenção corretos (90, 365, 2555)
- StorageClass GLACIER_IR em 90 dias
- Conformidade SOX (7 anos = 2555 dias antes de deletar)
- LocalFileStorage.apply_lifecycle_policy() retorna False
"""
import asyncio
import pytest


def test_get_lifecycle_config_returns_valid_structure():
    """S3Storage.get_lifecycle_config() retorna dict com chave 'Rules'."""
    from lia_audit.audit_storage import S3Storage

    storage = S3Storage(bucket="test-bucket", prefix="audit")
    config = storage.get_lifecycle_config()

    assert isinstance(config, dict)
    assert "Rules" in config
    assert isinstance(config["Rules"], list)
    assert len(config["Rules"]) == 1


def test_lifecycle_has_correct_retention_days():
    """Verifica 90 dias hot, 365 cold, 2555 delete."""
    from lia_audit.audit_storage import (
        S3Storage,
        AUDIT_RETENTION_DAYS_HOT,
        AUDIT_RETENTION_DAYS_COLD,
        AUDIT_RETENTION_DAYS_DELETE,
    )

    assert AUDIT_RETENTION_DAYS_HOT == 90
    assert AUDIT_RETENTION_DAYS_COLD == 365
    assert AUDIT_RETENTION_DAYS_DELETE == 2555

    storage = S3Storage(bucket="test-bucket")
    config = storage.get_lifecycle_config()
    rule = config["Rules"][0]

    transitions = rule["Transitions"]
    days_list = [t["Days"] for t in transitions]
    assert 90 in days_list
    assert 365 in days_list

    assert rule["Expiration"]["Days"] == 2555


def test_lifecycle_storage_class_glacier_ir():
    """Transição de 90 dias deve usar GLACIER_IR (Glacier Instant Retrieval)."""
    from lia_audit.audit_storage import S3Storage

    storage = S3Storage(bucket="test-bucket")
    config = storage.get_lifecycle_config()
    rule = config["Rules"][0]

    transitions_by_days = {t["Days"]: t["StorageClass"] for t in rule["Transitions"]}

    assert transitions_by_days[90] == "GLACIER_IR"
    assert transitions_by_days[365] == "DEEP_ARCHIVE"


def test_lifecycle_sox_compliance():
    """
    SOX/ISO 27001 exige no mínimo 7 anos (2555 dias) de retenção.
    O delete deve ocorrer em >= 2555 dias.
    """
    from lia_audit.audit_storage import S3Storage, AUDIT_RETENTION_DAYS_DELETE

    storage = S3Storage(bucket="test-bucket")
    config = storage.get_lifecycle_config()
    rule = config["Rules"][0]

    expiration_days = rule["Expiration"]["Days"]
    assert expiration_days >= 2555, (
        f"SOX compliance requer >= 2555 dias (7 anos), mas configurado para {expiration_days} dias"
    )

    # Constante também deve estar correta
    assert AUDIT_RETENTION_DAYS_DELETE >= 2555


def test_local_storage_lifecycle_returns_false():
    """LocalFileStorage.apply_lifecycle_policy() deve retornar False."""
    from lia_audit.audit_storage import LocalFileStorage

    storage = LocalFileStorage(base_dir="/tmp/test_audit_lifecycle")
    result = asyncio.run(storage.apply_lifecycle_policy())

    assert result is False
