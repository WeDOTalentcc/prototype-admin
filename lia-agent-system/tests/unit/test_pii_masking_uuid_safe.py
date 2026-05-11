"""
Test suite R1 (Task T-F) — `strip_pii_for_llm_prompt` deve ser UUID-aware.

Origem: bug "LIA pergunta company_id no chat" voltou (3ª vez) porque o regex
`PHONE_BR_PATTERN` em `app/shared/pii_masking.py:41` casa `\\d{4}[\\-\\s]?\\d{4}\\b`,
o que destrói qualquer UUID v4 — inclusive o UUID canônico da Demo Company
(`00000000-0000-4000-a000-000000000001`).

Ao destruir o UUID dentro do `tenant_context_snippet`, o LLM recebe contexto
incoerente e degrada para "qual é o ID da empresa?". Bug ortogonal a T-A/B/C/D/E
(nenhum daqueles testes passa o snippet pelo `strip_pii_for_llm_prompt`).

Contratos defendidos:
  1. UUIDs v4 sobrevivem intactos a `strip_pii_for_llm_prompt`.
  2. Telefones BR continuam sendo redigidos.
  3. UUIDs em diferentes contextos (sozinhos, com prefixo, em frase, múltiplos)
     todos sobrevivem.
"""
from __future__ import annotations

import re
import uuid

import pytest

from app.shared.pii_masking import strip_pii_for_llm_prompt

# Regex canônico de UUID v4 — usado para asserções de "preservação intacta".
_UUID_V4_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"


class TestUUIDSurvivesPIIStripping:
    """Contrato 1: UUID v4 NUNCA pode ser quebrado pelo PII strip."""

    def test_demo_company_uuid_survives_alone(self):
        result = strip_pii_for_llm_prompt(DEMO_COMPANY_UUID)
        assert DEMO_COMPANY_UUID in result, (
            f"UUID Demo Company foi destruído pelo PII strip. Resultado: {result!r}"
        )

    def test_demo_company_uuid_survives_in_sentence(self):
        text = f"O tenant atual é {DEMO_COMPANY_UUID} (Demo Company)."
        result = strip_pii_for_llm_prompt(text)
        assert DEMO_COMPANY_UUID in result, result

    def test_demo_company_uuid_survives_with_company_id_prefix(self):
        text = f"company_id={DEMO_COMPANY_UUID}"
        result = strip_pii_for_llm_prompt(text)
        assert DEMO_COMPANY_UUID in result, result

    @pytest.mark.parametrize("seed", list(range(50)))
    def test_50_random_uuid_v4_survive(self, seed):
        # uuid4 usa randomness do SO; garantimos cobertura ampla com 50 casos
        u = str(uuid.uuid4())
        text = f"tenant_id={u}; processando..."
        result = strip_pii_for_llm_prompt(text)
        assert u in result, (
            f"UUID v4 #{seed} ({u}) foi destruído. "
            f"Resultado: {result!r}"
        )

    def test_multiple_uuids_in_same_text_all_survive(self):
        u1 = str(uuid.uuid4())
        u2 = str(uuid.uuid4())
        text = f"company {u1} job {u2}"
        result = strip_pii_for_llm_prompt(text)
        assert u1 in result, result
        assert u2 in result, result

    def test_uuid_with_brackets_or_punctuation(self):
        text = f"[{DEMO_COMPANY_UUID}] - tenant ativo"
        result = strip_pii_for_llm_prompt(text)
        assert DEMO_COMPANY_UUID in result, result

    def test_tenant_snippet_realistic_shape(self):
        """Forma real do snippet emitido por TenantContextService.to_prompt_snippet."""
        snippet = (
            "### Contexto do Cliente\n"
            f"Empresa: Demo Company (id={DEMO_COMPANY_UUID})\n"
            "Setor: Tecnologia\n"
            "Plano: enterprise\n"
            "Timezone: America/Sao_Paulo"
        )
        result = strip_pii_for_llm_prompt(snippet)
        assert DEMO_COMPANY_UUID in result, result
        assert "Demo Company" in result
        assert "Tecnologia" in result


class TestPhoneBRStillRedacted:
    """Contrato 2: regressão — telefones BR continuam redigidos."""

    @pytest.mark.parametrize(
        "phone",
        [
            "+55 11 91234-5678",
            "(11) 91234-5678",
            "11 91234-5678",
            # NB: "11912345678" (11 dígitos puros) é capturado pelo CPF_PATTERN
            # (comportamento pré-existente), não pelo PHONE — não testamos esse formato aqui.
            "1234-5678",  # formato curto sem DDD
        ],
    )
    def test_phone_br_is_stripped(self, phone):
        text = f"Contato: {phone}"
        result = strip_pii_for_llm_prompt(text)
        assert "[TELEFONE REMOVIDO]" in result, (
            f"Telefone {phone!r} deveria ter sido redigido. Resultado: {result!r}"
        )

    def test_phone_and_uuid_coexist(self):
        """Telefone redigido mas UUID intacto na mesma string."""
        text = f"company={DEMO_COMPANY_UUID}; suporte 11 91234-5678"
        result = strip_pii_for_llm_prompt(text)
        assert DEMO_COMPANY_UUID in result, result
        assert "[TELEFONE REMOVIDO]" in result, result


class TestOtherPIIStillRedacted:
    """Contrato 3: outros PII continuam funcionando."""

    def test_email_still_stripped(self):
        result = strip_pii_for_llm_prompt(
            f"contact={DEMO_COMPANY_UUID} email john@example.com"
        )
        assert DEMO_COMPANY_UUID in result
        assert "[EMAIL REMOVIDO]" in result

    def test_cpf_still_stripped(self):
        result = strip_pii_for_llm_prompt(
            f"id={DEMO_COMPANY_UUID} cpf 123.456.789-00"
        )
        assert DEMO_COMPANY_UUID in result
        assert "[CPF REMOVIDO]" in result
