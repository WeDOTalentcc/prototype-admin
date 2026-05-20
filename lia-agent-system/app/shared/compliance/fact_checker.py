"""
FactChecker - Post-response validation middleware.

Validates numeric claims made by AI responses against real data sources.
Checks salary ranges, candidate counts, dates, and other verifiable claims.

Adds confidence_verified flag to responses for transparency.
Part of the 3-pillar compliance architecture (LGPD, SOX, EU AI Act).
"""
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class FactCheckClaim:
    claim_type: str
    original_value: Any
    verified_value: Any | None = None
    is_verified: bool = False
    is_accurate: bool | None = None
    deviation_pct: float | None = None
    source: str | None = None
    notes: str = ""


@dataclass
class FactCheckResult:
    confidence_verified: bool
    total_claims: int = 0
    verified_claims: int = 0
    accurate_claims: int = 0
    inaccurate_claims: int = 0
    unverifiable_claims: int = 0
    claims: list[FactCheckClaim] = field(default_factory=list)
    overall_accuracy: float = 1.0
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def add_claim(self, claim: FactCheckClaim) -> None:
        self.claims.append(claim)
        self.total_claims += 1
        if claim.is_verified:
            self.verified_claims += 1
            if claim.is_accurate:
                self.accurate_claims += 1
            elif claim.is_accurate is False:
                self.inaccurate_claims += 1
        else:
            self.unverifiable_claims += 1
        self._recalculate_accuracy()

    def _recalculate_accuracy(self) -> None:
        if self.verified_claims > 0:
            self.overall_accuracy = self.accurate_claims / self.verified_claims
        else:
            self.overall_accuracy = 1.0
        self.confidence_verified = self.verified_claims > 0

    def to_metadata(self) -> dict[str, Any]:
        return {
            "fact_check": {
                "confidence_verified": self.confidence_verified,
                "total_claims": self.total_claims,
                "verified_claims": self.verified_claims,
                "accurate_claims": self.accurate_claims,
                "inaccurate_claims": self.inaccurate_claims,
                "overall_accuracy": round(self.overall_accuracy, 3),
                "checked_at": self.checked_at.isoformat(),
            }
        }


SALARY_PATTERN = re.compile(
    r"R\$\s*([\d.,]+)(?:\s*(?:a|até|-)\s*R\$\s*([\d.,]+))?",
    re.IGNORECASE | re.UNICODE,
)
CANDIDATE_COUNT_PATTERN = re.compile(
    r"(\d+)\s*candidatos?",
    re.IGNORECASE | re.UNICODE,
)
PERCENTAGE_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*%",
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(
    r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})",
)

REASONABLE_SALARY_RANGE = (1_500, 200_000)
MAX_CANDIDATE_COUNT = 50_000


class FactChecker:
    def __init__(self, data_sources: dict[str, Any] | None = None):
        self._data_sources = data_sources or {}

    def check_response(
        self,
        response_text: str,
        context: dict[str, Any] | None = None,
    ) -> FactCheckResult:
        result = FactCheckResult(confidence_verified=False)
        context = context or {}

        self._check_salary_claims(response_text, context, result)
        self._check_candidate_counts(response_text, context, result)
        self._check_percentage_claims(response_text, context, result)
        self._check_date_claims(response_text, context, result)

        if result.inaccurate_claims > 0:
            logger.warning(
                f"FactChecker found {result.inaccurate_claims} inaccurate claims "
                f"out of {result.total_claims} total"
            )

        return result

    def _parse_br_number(self, text: str) -> float:
        cleaned = text.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            # T-04 Tipo D: BR number parse is best-effort for fact-checking
            # numeric claims; returning 0.0 makes the downstream "abs() > 5"
            # comparison harmless (won't flag a fake mismatch).
            return 0.0

    def _check_salary_claims(
        self, text: str, context: dict[str, Any], result: FactCheckResult
    ) -> None:
        for match in SALARY_PATTERN.finditer(text):
            low = self._parse_br_number(match.group(1))
            high = self._parse_br_number(match.group(2)) if match.group(2) else low

            claim = FactCheckClaim(
                claim_type="salary",
                original_value={"low": low, "high": high},
            )

            min_sal, max_sal = REASONABLE_SALARY_RANGE
            if low < min_sal or high > max_sal or (high > 0 and low > high):
                claim.is_verified = True
                claim.is_accurate = False
                claim.notes = f"Salary outside reasonable range ({min_sal}-{max_sal})"
            else:
                claim.is_verified = True
                claim.is_accurate = True

            expected_range = context.get("expected_salary_range")
            if expected_range and isinstance(expected_range, dict):
                exp_low = expected_range.get("min", 0)
                expected_range.get("max", float("inf"))
                if low > 0 and exp_low > 0:
                    deviation = abs(low - exp_low) / exp_low
                    claim.deviation_pct = round(deviation * 100, 1)
                    claim.source = "context_salary_range"
                    if deviation > 0.5:
                        claim.is_accurate = False
                        claim.notes = f"Salary deviates {claim.deviation_pct}% from expected"

            result.add_claim(claim)

    def _check_candidate_counts(
        self, text: str, context: dict[str, Any], result: FactCheckResult
    ) -> None:
        for match in CANDIDATE_COUNT_PATTERN.finditer(text):
            count = int(match.group(1))
            claim = FactCheckClaim(
                claim_type="candidate_count",
                original_value=count,
            )

            if count > MAX_CANDIDATE_COUNT:
                claim.is_verified = True
                claim.is_accurate = False
                claim.notes = f"Count exceeds maximum ({MAX_CANDIDATE_COUNT})"
            elif count == 0:
                claim.is_verified = True
                claim.is_accurate = True
                claim.notes = "Zero count — may be valid"
            else:
                claim.is_verified = True
                claim.is_accurate = True

            expected_count = context.get("expected_candidate_count")
            if expected_count and isinstance(expected_count, (int, float)):
                deviation = abs(count - expected_count) / max(expected_count, 1)
                claim.deviation_pct = round(deviation * 100, 1)
                claim.source = "context_candidate_count"
                if deviation > 1.0:
                    claim.is_accurate = False
                    claim.notes = f"Count deviates {claim.deviation_pct}% from expected"

            result.add_claim(claim)

    def _check_percentage_claims(
        self, text: str, context: dict[str, Any], result: FactCheckResult
    ) -> None:
        for match in PERCENTAGE_PATTERN.finditer(text):
            value = float(match.group(1).replace(",", "."))
            claim = FactCheckClaim(
                claim_type="percentage",
                original_value=value,
            )

            if value < 0 or value > 100:
                claim.is_verified = True
                claim.is_accurate = False
                claim.notes = "Percentage outside 0-100 range"
            else:
                claim.is_verified = True
                claim.is_accurate = True

            result.add_claim(claim)

    def _check_date_claims(
        self, text: str, context: dict[str, Any], result: FactCheckResult
    ) -> None:
        for match in DATE_PATTERN.finditer(text):
            day, month, year = match.groups()
            year_int = int(year)
            if year_int < 100:
                year_int += 2000

            claim = FactCheckClaim(
                claim_type="date",
                original_value=f"{day}/{month}/{year}",
            )

            try:
                parsed = datetime(year_int, int(month), int(day))
                claim.is_verified = True
                if parsed.year < 2020 or parsed.year > 2030:
                    claim.is_accurate = False
                    claim.notes = f"Date year {parsed.year} seems unreasonable for recruitment context"
                else:
                    claim.is_accurate = True
                claim.verified_value = parsed.isoformat()
            except (ValueError, OverflowError):
                claim.is_verified = True
                claim.is_accurate = False
                claim.notes = "Invalid date"

            result.add_claim(claim)

    # ------------------------------------------------------------------
    # Granular public methods (V5 parity — Sprint H)
    # ------------------------------------------------------------------

    def verify_count_claim(
        self,
        response_text: str,
        expected_count: int | None = None,
        tolerance_pct: float = 10.0,
    ) -> FactCheckClaim:
        """
        Verifica a primeira claim de contagem (N candidatos) no texto.
        Compara contra `expected_count` se fornecido, dentro de `tolerance_pct`.
        Retorna FactCheckClaim isolada — útil para validação granular.
        """
        match = CANDIDATE_COUNT_PATTERN.search(response_text)
        if not match:
            return FactCheckClaim(
                claim_type="candidate_count",
                original_value=None,
                is_verified=False,
                notes="No count claim found in text",
            )

        count = int(match.group(1))
        claim = FactCheckClaim(claim_type="candidate_count", original_value=count)

        if count > MAX_CANDIDATE_COUNT:
            claim.is_verified = True
            claim.is_accurate = False
            claim.notes = f"Count {count} exceeds maximum ({MAX_CANDIDATE_COUNT})"
            return claim

        claim.is_verified = True
        claim.is_accurate = True

        if expected_count is not None:
            deviation = abs(count - expected_count) / max(expected_count, 1) * 100
            claim.deviation_pct = round(deviation, 1)
            claim.source = "expected_count"
            if deviation > tolerance_pct:
                claim.is_accurate = False
                claim.notes = (
                    f"Count {count} deviates {claim.deviation_pct}% from "
                    f"expected {expected_count} (tolerance {tolerance_pct}%)"
                )

        return claim

    def verify_average_claim(
        self,
        response_text: str,
        expected_average: float | None = None,
        tolerance_pct: float = 20.0,
        claim_type: str = "average",
    ) -> FactCheckClaim:
        """
        Verifica a primeira claim de média/percentual no texto.
        Usa PERCENTAGE_PATTERN. Compara contra `expected_average` se fornecido.
        `claim_type` pode ser 'average_score', 'average_salary', etc.
        """
        match = PERCENTAGE_PATTERN.search(response_text)
        if not match:
            return FactCheckClaim(
                claim_type=claim_type,
                original_value=None,
                is_verified=False,
                notes="No percentage/average claim found in text",
            )

        value = float(match.group(1).replace(",", "."))
        claim = FactCheckClaim(claim_type=claim_type, original_value=value)

        if value < 0 or value > 100:
            claim.is_verified = True
            claim.is_accurate = False
            claim.notes = f"Value {value} outside 0-100 range"
            return claim

        claim.is_verified = True
        claim.is_accurate = True

        if expected_average is not None:
            deviation = abs(value - expected_average) / max(abs(expected_average), 1) * 100
            claim.deviation_pct = round(deviation, 1)
            claim.source = "expected_average"
            if deviation > tolerance_pct:
                claim.is_accurate = False
                claim.notes = (
                    f"Average {value} deviates {claim.deviation_pct}% from "
                    f"expected {expected_average} (tolerance {tolerance_pct}%)"
                )

        return claim

    def verify_top_candidates_claim(
        self,
        response_text: str,
        expected_top_n: int | None = None,
        max_reasonable_top: int = 20,
    ) -> FactCheckClaim:
        """
        Verifica se a resposta afirma um número razoável de top candidatos.
        Detecta padrões como "top 5", "os 3 melhores", "primeiros 10 candidatos".
        Compara contra `expected_top_n` se fornecido.
        """
        TOP_PATTERN = re.compile(
            r"(?:top|os?|primeiros?)\s+(\d+)\s*(?:candidatos?|melhores?|perfis?)?",
            re.IGNORECASE | re.UNICODE,
        )
        match = TOP_PATTERN.search(response_text)
        if not match:
            return FactCheckClaim(
                claim_type="top_candidates",
                original_value=None,
                is_verified=False,
                notes="No top-N candidates claim found in text",
            )

        n = int(match.group(1))
        claim = FactCheckClaim(claim_type="top_candidates", original_value=n)

        if n <= 0 or n > max_reasonable_top:
            claim.is_verified = True
            claim.is_accurate = False
            claim.notes = f"Top-N value {n} outside reasonable range (1-{max_reasonable_top})"
            return claim

        claim.is_verified = True
        claim.is_accurate = True

        if expected_top_n is not None and n != expected_top_n:
            claim.deviation_pct = abs(n - expected_top_n) / max(expected_top_n, 1) * 100
            claim.source = "expected_top_n"
            claim.is_accurate = False
            claim.notes = f"Claimed top-{n} but expected top-{expected_top_n}"

        return claim


    # ------------------------------------------------------------------
    # LIA-C06 - Domain-specific validator registry
    # ------------------------------------------------------------------

    _domain_validators: dict[str, list[Callable]] = {}

    @classmethod
    def register_validator(
        cls,
        domain_id: str,
        validator_fn: Callable,
    ) -> None:
        """Registra um validador domain-specific.

        Args:
            domain_id: ID do dominio (ex: 'cv_screening', 'analytics', 'sourcing')
            validator_fn: coroutine async que recebe (claim_text, context_data)
                          e retorna mensagem de discrepancia ou None se ok.

        Exemplo::

            FactChecker.register_validator('cv_screening', validate_cv_score_claim)
        """
        if domain_id not in cls._domain_validators:
            cls._domain_validators[domain_id] = []
        if validator_fn not in cls._domain_validators[domain_id]:
            cls._domain_validators[domain_id].append(validator_fn)
        logger.debug(
            "Registered domain validator '%s' for domain '%s'",
            getattr(validator_fn, "__name__", repr(validator_fn)),
            domain_id,
        )

    async def check_response_with_domain(
        self,
        response_text: str,
        context_data: dict[str, Any],
        domain_id: str,
    ) -> "FactCheckResult":
        """Verifica resposta usando validadores genericos + validadores domain-specific.

        Executa primeiro check_response() (sincrono) para claims genericas
        (salario, contagem, percentual, data) e depois aplica os validadores
        assincronos registrados para o dominio informado.

        Args:
            response_text: Texto da resposta gerada pelo agente LIA.
            context_data:  Dicionario com dados reais de contexto.
            domain_id:     ID do dominio para selecao de validadores.

        Returns:
            FactCheckResult enriquecido com claims domain-specific.
        """
        result = self.check_response(response_text, context_data)

        for validator in self._domain_validators.get(domain_id, []):
            try:
                discrepancy = await validator(response_text, context_data)
                if discrepancy:
                    domain_claim = FactCheckClaim(
                        claim_type=f"domain_{domain_id}",
                        original_value=discrepancy,
                        is_verified=True,
                        is_accurate=False,
                        notes=f"[{domain_id}] {discrepancy}",
                        source=getattr(validator, "__name__", "domain_validator"),
                    )
                    result.add_claim(domain_claim)
                    logger.warning(
                        "Domain validator '%s' found discrepancy: %s",
                        getattr(validator, "__name__", domain_id),
                        discrepancy,
                    )
            except Exception as e:
                logger.warning(
                    "Domain validator '%s' for domain '%s' raised: %s",
                    getattr(validator, "__name__", repr(validator)),
                    domain_id,
                    e,
                )

        return result

    def register_data_source(self, name: str, source: Any) -> None:
        self._data_sources[name] = source

    def __repr__(self) -> str:
        return f"<FactChecker sources={list(self._data_sources.keys())}>"
