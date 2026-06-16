"""
Testes de validacao mod11 de CNPJ no schema CompanyProfileUpdate.
P2 Audit 2026-05-24.
"""
import pytest
from pydantic import ValidationError
from app.schemas.company import CompanyProfileUpdate

VALID_CNPJS = [
    "11.222.333/0001-81",   # formatado, valido
    "11222333000181",        # so digitos, valido
    "45.997.418/0001-53",   # outro valido real
]

INVALID_CNPJS = [
    "11.111.111/1111-11",   # sequencia repetida
    "00.000.000/0000-00",   # zeros
    "12345678",              # muito curto
    "123456789012345",       # muito longo
    "11.222.333/0001-99",   # digitos verificadores errados
]


@pytest.mark.parametrize("cnpj", VALID_CNPJS)
def test_valid_cnpj_accepted(cnpj):
    obj = CompanyProfileUpdate(name="Test", cnpj=cnpj)
    assert obj.cnpj is not None
    assert len(obj.cnpj) == 14  # retorna so digitos


@pytest.mark.parametrize("cnpj", INVALID_CNPJS)
def test_invalid_cnpj_rejected(cnpj):
    with pytest.raises(ValidationError) as exc_info:
        CompanyProfileUpdate(name="Test", cnpj=cnpj)
    assert "CNPJ" in str(exc_info.value)


def test_cnpj_none_accepted():
    obj = CompanyProfileUpdate(name="Test", cnpj=None)
    assert obj.cnpj is None


def test_hr_email_valid():
    obj = CompanyProfileUpdate(name="Test", hr_email="rh@empresa.com")
    assert obj.hr_email == "rh@empresa.com"


def test_hr_email_invalid():
    with pytest.raises(ValidationError):
        CompanyProfileUpdate(name="Test", hr_email="nao_e_email")
