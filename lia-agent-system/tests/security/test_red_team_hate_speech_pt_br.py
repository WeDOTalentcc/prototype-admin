"""
Red-team test for W1-007 · HateSpeechGuard pt-BR 5 layers adversarial.

Tests cobertura adversarial específica pt-BR:
- L1 NFKD normalize (acentos / case)
- L2 leetspeak (1337, @, !, etc)
- L3 lookalike Cyrillic (а=a, е=e, о=o)
- L4 zero-width chars (U+200B, etc)
- L5 spaced-letters (r a c i s t a)

Plus c3b_layer wiring: pre_compliance ANTES de PII strip
(slur normalizado em pseudo-PII passaria por PII filter sem ser caught).

TDD red→green:
- RED antes da implementação (HateSpeechGuard import fails)
- GREEN após:
  1. app/shared/compliance/hate_speech_guard.py criado
  2. c3b_layer.pre_compliance wire (pre PII strip)

Sensor anti-regressão: scripts/check_hate_speech_guard_wired.py
"""
import asyncio

import pytest


class TestHateSpeechGuardBasic:
    """W1-007 gap 1 · HateSpeechGuard class deve existir e detectar slurs canonical."""

    def test_module_importable(self) -> None:
        """HateSpeechGuard module deve existir em app/shared/compliance/."""
        from app.shared.compliance.hate_speech_guard import (  # noqa: F401
            HateSpeechGuard,
            HateSpeechCheckResult,
            HateCategory,
        )

    def test_clean_input_allowed(self) -> None:
        """Sanity check: input legítimo NÃO bloqueado."""
        from app.shared.compliance.hate_speech_guard import HateSpeechGuard

        guard = HateSpeechGuard()
        result = guard.check("Quais candidatos têm experiência em Python?")
        assert result.is_blocked is False

    def test_racial_slur_pt_br_blocked(self) -> None:
        """Slur racial direto pt-BR deve ser bloqueado."""
        from app.shared.compliance.hate_speech_guard import (
            HateSpeechGuard,
            HateCategory,
        )

        guard = HateSpeechGuard()
        # Uso "crioulo + adj negativo" — pattern canonical
        # Match pode ser RACIAL_SLUR (direct) OU DEHUMANIZATION (pretinho/crioulo+adj)
        # ordem do registry: DEHUMANIZATION primeiro
        result = guard.check("Esse crioulo nojento é incompetente")
        assert result.is_blocked is True
        assert result.category in (HateCategory.RACIAL_SLUR, HateCategory.DEHUMANIZATION)

    def test_homophobic_slur_blocked(self) -> None:
        """Slur homofóbico deve ser bloqueado."""
        from app.shared.compliance.hate_speech_guard import (
            HateSpeechGuard,
            HateCategory,
        )

        guard = HateSpeechGuard()
        result = guard.check("Esse viado não merece a vaga")
        assert result.is_blocked is True
        assert result.category == HateCategory.SEXUAL_ORIENTATION_SLUR

    def test_dehumanization_pattern_blocked(self) -> None:
        """Pattern dehumanization (preto + macaco) deve ser bloqueado."""
        from app.shared.compliance.hate_speech_guard import (
            HateSpeechGuard,
            HateCategory,
        )

        guard = HateSpeechGuard()
        result = guard.check("Volta pra África, preto macaco")
        assert result.is_blocked is True
        assert result.category in (HateCategory.DEHUMANIZATION, HateCategory.RACIAL_SLUR)


class TestHateSpeechGuardAdversarial:
    """W1-007 gap 2 · 5 layers adversarial normalization."""

    def test_leetspeak_bypass_detected(self) -> None:
        """L2 leetspeak: v14d0 → viado deve ser bloqueado."""
        from app.shared.compliance.hate_speech_guard import HateSpeechGuard

        guard = HateSpeechGuard()
        # viado com leetspeak (1=i, 4=a, 0=o)
        result = guard.check("Esse v14d0 nojento")
        assert result.is_blocked is True
        assert result.adversarial_normalization is True

    def test_lookalike_cyrillic_bypass_detected(self) -> None:
        """L3 Cyrillic lookalike: 'crioulо' com 'о' cirílico (U+043E)."""
        from app.shared.compliance.hate_speech_guard import HateSpeechGuard

        guard = HateSpeechGuard()
        # 'crioulо' com 'о' cirílico (U+043E), não 'o' latino (U+006F)
        result = guard.check("crioulо nojento safado")
        assert result.is_blocked is True
        assert result.adversarial_normalization is True

    def test_zero_width_bypass_detected(self) -> None:
        """L4 zero-width: 'cri​oulo' com U+200B entre letras."""
        from app.shared.compliance.hate_speech_guard import HateSpeechGuard

        guard = HateSpeechGuard()
        # U+200B inserido em 'crioulo'
        result = guard.check("cri​oulo​ nojento​")
        assert result.is_blocked is True
        assert result.adversarial_normalization is True

    def test_spaced_letters_bypass_detected(self) -> None:
        """L5 spaced-letters: 'v i a d o' deve normalizar pra 'viado'."""
        from app.shared.compliance.hate_speech_guard import HateSpeechGuard

        guard = HateSpeechGuard()
        # spaced letters bypass (>= 4 letras com espaços)
        result = guard.check("Esse v i a d o nojento")
        assert result.is_blocked is True
        assert result.adversarial_normalization is True


class TestHateSpeechWiringInC3bLayer:
    """W1-007 gap 3 · c3b_layer.pre_compliance deve chamar HateSpeechGuard."""

    @pytest.mark.asyncio
    async def test_hate_speech_blocked_via_c3b_pre_compliance(self) -> None:
        """
        Input com slur deve ser bloqueado em c3b_layer.pre_compliance.

        Hoje: passa (c3b nem chama HateSpeechGuard).
        Após fix: bloqueado com hate_speech_blocked=True + reason.
        """
        from app.shared.compliance.c3b_layer import pre_compliance, PreComplianceResult

        slur_input = "Esse crioulo nojento é incompetente"
        result: PreComplianceResult = await pre_compliance(
            message=slur_input,
            company_id="test-company",
            domain="generic_chat",
        )
        # Esperamos campo novo `hate_speech_blocked`
        assert hasattr(result, "hate_speech_blocked"), (
            "PreComplianceResult should expose hate_speech_blocked field after W1-007"
        )
        assert result.hate_speech_blocked is True, (
            f"Hate speech slur must be blocked at c3b pre. "
            f"Got hate_speech_blocked={result.hate_speech_blocked}, "
            f"block_reason={result.block_reason!r}"
        )

    @pytest.mark.asyncio
    async def test_clean_input_passes_through_c3b(self) -> None:
        """Sanity: input limpo NÃO é falsamente bloqueado por hate speech."""
        from app.shared.compliance.c3b_layer import pre_compliance

        result = await pre_compliance(
            message="Quero ver os candidatos com Python",
            company_id="test-company",
            domain="generic_chat",
        )
        hate_blocked = getattr(result, "hate_speech_blocked", False)
        assert hate_blocked is False


class TestHateSpeechGuardEducationalMessage:
    """W1-007 · educational_message must be canonical + PT-BR."""

    def test_educational_message_present_on_block(self) -> None:
        """Block result deve ter educational_message PT-BR explicando motivo."""
        from app.shared.compliance.hate_speech_guard import HateSpeechGuard

        guard = HateSpeechGuard()
        result = guard.check("crioulo nojento")
        assert result.is_blocked is True
        assert result.educational_message is not None
        assert len(result.educational_message) > 20
        # Deve mencionar dignidade/respeito (canonical msg)
        msg_lower = result.educational_message.lower()
        assert any(
            keyword in msg_lower
            for keyword in ("dignidade", "respeit", "ofensiv", "discrimin")
        ), f"Educational message must explain: {result.educational_message!r}"
