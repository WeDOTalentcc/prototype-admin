# Diagnóstico Comparativo FairnessGuard — v5 vs LIA Replit

**Data:** 31/03/2026
**Autor:** Análise automatizada com leitura direta de código via GitHub API (v5) e filesystem (LIA Replit)
**Escopo:** Fairness, bias e compliance anti-discriminatória — inventário completo, comparação dimensional, riscos regulatórios, dispersão arquitetural e recomendações

---

## 1. Inventário Completo — recruiter_agent_v5 (GitHub)

### 1.1 Estrutura Geral de Fairness no v5

O v5 possui **2 arquivos `fairness.py`**, cada um dentro de um domínio específico:
- `src/domains/jobs/fairness.py` — `JobFairnessGuard`
- `src/domains/sourced_profile_sourcing/fairness.py` — `FairnessGuard` + `FairnessMetrics` + `anonymize_for_llm`

**Estes arquivos NÃO são compartilhados transversalmente.** Cada um pertence ao seu domínio e contém regras diferentes. **Nenhum `domain.py` importa o fairness.py** — a integração acontece apenas nas **actions e agents** específicos.

**Não existe** `src/services/fairness_checker.py` ou qualquer serviço compartilhado de fairness em `src/services/`. A pasta `src/services/` contém: `pii_filter.py` (logging only), `security.py` (prompt injection), `audit/` (audit_callback sem fairness), entre 39+ outros serviços — nenhum deles de fairness.

---

### 1.2 `src/domains/jobs/fairness.py` — JobFairnessGuard

**Caminho exato:** `src/domains/jobs/fairness.py`
**Leitura:** Direta via GitHub API em 31/03/2026

```python
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

BLOCKED_FILTERS = frozenset({
    "gender", "genero", "sexo",
    "age", "idade", "birth_date", "data_nascimento",
    "race", "raca", "raça", "ethnicity", "etnia",
    "marital", "estado_civil",
    "religion", "religiao", "religião",
})

PCD_CONTEXT_REQUIRED = frozenset({"pcd", "disability", "deficiencia", "deficiência"})

DISCLAIMER_MATCHING = (
    "⚠️ **Aviso de Fairness**: Este matching e baseado em fit tecnico. "
    "NAO deve ser usado como decisao final. Recomenda-se revisao humana "
    "considerando contexto individual de cada candidato."
)

DISCLAIMER_BULK_ACTION = (
    "⚠️ **Aviso**: Acoes em lote afetam multiplos candidatos. Certifique-se "
    "de que a selecao esta correta antes de confirmar."
)


class JobFairnessGuard:

    @staticmethod
    def check_filters(params: Dict[str, Any], job_context: Optional[Dict] = None
                      ) -> Tuple[bool, Optional[str]]:
        where = params.get("where", {})
        if not where:
            return True, None

        for key in where:
            key_lower = key.lower()

            if key_lower in BLOCKED_FILTERS:
                logger.warning(f"[FAIRNESS] Blocked filter: {key}")
                return False, (
                    f"🚫 O filtro '{key}' nao e permitido por politicas de diversidade "
                    "e inclusao. Filtros por genero, idade, raca, religiao ou estado "
                    "civil sao bloqueados."
                )

            if key_lower in PCD_CONTEXT_REQUIRED:
                has_disabilities = (
                    job_context.get("disabilities", False) if job_context else False
                )
                if not has_disabilities:
                    return False, (
                        "🚫 Filtro PCD so e permitido quando a vaga tem o campo "
                        "'disabilities=true'. Essa vaga nao possui essa configuracao."
                    )

        return True, None

    @staticmethod
    def get_matching_disclaimer() -> str:
        return DISCLAIMER_MATCHING

    @staticmethod
    def get_bulk_action_disclaimer() -> str:
        return DISCLAIMER_BULK_ACTION
```

**Quem importa este arquivo (verificado):**
| Arquivo consumidor | Import | Uso |
|---|---|---|
| `src/domains/jobs/actions/matching.py` | `from src.domains.jobs.fairness import JobFairnessGuard` | `check_filters()` antes de matching + `get_matching_disclaimer()` no resultado |
| `src/domains/jobs/actions/mutations.py` | `from src.domains.jobs.fairness import JobFairnessGuard` | `get_bulk_action_disclaimer()` em bulk actions |

**Quem NÃO importa (verificado — 0 referências a fairness):**
- `src/domains/jobs/domain.py` (533 linhas) — ❌
- `src/domains/jobs/dispatcher.py` — ❌
- `src/domains/jobs/actions/analytics.py` — ❌
- `src/domains/jobs/actions/query.py` — ❌
- `src/domains/jobs/actions/suggestions.py` — ❌
- `src/domains/jobs/actions/conversational.py` — ❌

---

### 1.3 `src/domains/sourced_profile_sourcing/fairness.py` — FairnessGuard + FairnessMetrics + anonymize_for_llm

**Caminho exato:** `src/domains/sourced_profile_sourcing/fairness.py`
**Leitura:** Direta via GitHub API em 31/03/2026

```python
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FairnessMetrics:
    _blocked_count: int = 0
    _warnings_count: int = 0
    _pii_scrubbed_count: int = 0
    _allowed_exceptions: List[Dict] = []
    _max_exceptions_log: int = 1000

    @classmethod
    def record_block(cls, filter_key: str, reason: str = ""):
        cls._blocked_count += 1
        logger.warning(
            f"[FAIRNESS_METRIC] blocked_filter: key={filter_key} reason={reason}")

    @classmethod
    def record_warning(cls, filter_key: str):
        cls._warnings_count += 1
        logger.info(f"[FAIRNESS_METRIC] warning_issued: key={filter_key}")

    @classmethod
    def record_pii_scrub(cls, field_name: str):
        cls._pii_scrubbed_count += 1
        logger.debug(f"[FAIRNESS_METRIC] pii_scrubbed: field={field_name}")

    @classmethod
    def record_exception_allowed(cls, filter_key: str, justification: str,
                                  user_id: str = None):
        if len(cls._allowed_exceptions) >= cls._max_exceptions_log:
            cls._allowed_exceptions = cls._allowed_exceptions[-500:]
        cls._allowed_exceptions.append({
            "timestamp": datetime.now().isoformat(),
            "filter": filter_key,
            "justification": justification,
            "user_id": user_id
        })
        logger.warning(
            f"[FAIRNESS_AUDIT] sensitive_filter_allowed: key={filter_key} "
            f"justification={justification} user={user_id}")

    @classmethod
    def get_stats(cls) -> Dict:
        return {
            "blocked_count": cls._blocked_count,
            "warnings_count": cls._warnings_count,
            "pii_scrubbed_count": cls._pii_scrubbed_count,
            "exceptions_allowed": len(cls._allowed_exceptions)
        }


class SensitiveAttribute(str, Enum):
    GENDER = "gender"
    AGE = "age"
    RACE = "race"
    ETHNICITY = "ethnicity"
    DISABILITY = "disability"
    MARITAL_STATUS = "marital_status"
    RELIGION = "religion"
    NATIONALITY = "nationality"


SENSITIVE_FILTER_KEYS = {
    "gender", "genero", "sexo",
    "age", "idade", "birth_date", "data_nascimento",
    "race", "raca", "raça", "ethnicity", "etnia",
    "pcd", "disability", "deficiencia", "deficiência",
    "marital", "estado_civil",
    "religion", "religiao", "religião",
}


@dataclass
class FairnessWarning:
    attribute: str
    message: str
    severity: str
    recommendation: str


class FairnessGuard:

    DISCLAIMER_DISCARD = (
        "⚠️ **Aviso de Fairness**: Esta análise é baseada apenas em fit técnico "
        "e score algorítmico. NÃO deve ser usada como decisão final de descarte. "
        "Recomenda-se revisão humana considerando contexto individual de cada candidato."
    )

    DISCLAIMER_RANKING = (
        "⚠️ **Aviso**: Este ranking é uma sugestão baseada em critérios técnicos. "
        "Fatores como fit cultural, potencial de crescimento e diversidade "
        "devem ser considerados na decisão final."
    )

    DISCLAIMER_HIRING_PROBABILITY = (
        "⚠️ **Nota**: 'Probabilidade de contratação' é uma estimativa baseada "
        "em padrões históricos e pode conter vieses. Use apenas como referência."
    )

    @classmethod
    def check_sensitive_filters(cls, params: Dict[str, Any]) -> List[FairnessWarning]:
        warnings = []
        for key, value in params.items():
            if key.lower() in SENSITIVE_FILTER_KEYS and value is not None:
                warnings.append(FairnessWarning(
                    attribute=key,
                    message=f"Filtro por '{key}' pode violar políticas de igualdade",
                    severity="high",
                    recommendation="Considere remover este filtro ou documentar "
                                   "justificativa legal"
                ))
                FairnessMetrics.record_warning(key)
                logger.warning(f"🚨 Sensitive filter detected: {key}={value}")
        return warnings

    @classmethod
    def get_filter_warning_message(cls, warnings: List[FairnessWarning]
                                    ) -> Optional[str]:
        if not warnings:
            return None
        lines = ["⚠️ **Alerta de Compliance**\n"]
        for w in warnings:
            lines.append(f"• **{w.attribute}**: {w.message}")
            lines.append(f"  → {w.recommendation}\n")
        lines.append(
            "\n*Filtros por atributos protegidos podem violar LGPD/EEO. "
            "Consulte seu departamento jurídico.*"
        )
        return "\n".join(lines)

    @classmethod
    def should_block_filter(cls, key: str, allow_exception: bool = False,
                             justification: str = None, user_id: str = None
                             ) -> bool:
        blocked = {
            "race", "raca", "raça", "ethnicity", "etnia",
            "religion", "religiao", "religião",
            "gender", "genero", "gênero", "sexo",
            "age", "idade", "birth_date", "data_nascimento",
            "pcd", "disability", "deficiencia", "deficiência"
        }
        if key.lower() not in blocked:
            return False
        if allow_exception and justification:
            FairnessMetrics.record_exception_allowed(key, justification, user_id)
            return False
        FairnessMetrics.record_block(key, "no_exception_provided")
        return True

    @classmethod
    def add_discard_disclaimer(cls, message: str) -> str:
        return f"{message}\n\n---\n{cls.DISCLAIMER_DISCARD}"

    @classmethod
    def add_ranking_disclaimer(cls, message: str) -> str:
        return f"{message}\n\n---\n{cls.DISCLAIMER_RANKING}"

    @classmethod
    def add_hiring_probability_disclaimer(cls, analysis: Dict) -> Dict:
        if "hiring_probability" in analysis:
            analysis["_disclaimer"] = cls.DISCLAIMER_HIRING_PROBABILITY
        return analysis


def anonymize_for_llm(
    candidates: List[Dict],
    fields_to_keep: List[str] = None
) -> tuple[List[Dict], Dict[str, str]]:
    if fields_to_keep is None:
        fields_to_keep = ["score", "sourcing_score",
                          "total_experience_years", "skills", "city"]
    anonymized = []
    id_mapping = {}
    for i, c in enumerate(candidates, 1):
        code = f"C{i:03d}"
        anon = {"candidate_code": code}
        cand_id = c.get("id")
        if cand_id:
            id_mapping[code] = str(cand_id)
        for field in fields_to_keep:
            if field not in c:
                continue
            if field in ("analysis", "ai_analysis"):
                anon[field] = _sanitize_analysis(c[field])
            else:
                anon[field] = c[field]
        anonymized.append(anon)
    return anonymized, id_mapping


def _sanitize_analysis(analysis) -> Dict:
    if not isinstance(analysis, dict):
        return {}
    safe_structured_keys = {"highlights", "red_flags", "skills_assessment"}
    sanitized = {}
    for key, value in analysis.items():
        if key not in safe_structured_keys:
            continue
        if isinstance(value, list):
            sanitized[key] = [_sanitize_item(item) for item in value[:3]]
        elif isinstance(value, dict):
            sanitized[key] = {k: v for k, v in value.items()
                              if k in {"strong", "weak", "missing", "score", "level"}
                              and isinstance(v, (list, int, float))}
    return sanitized


def _sanitize_item(item) -> Any:
    if isinstance(item, dict):
        safe = {}
        for k, v in item.items():
            if k in {"severity", "type", "category"}:
                safe[k] = v
            elif k == "description" and isinstance(v, str):
                safe[k] = _scrub_pii(v)
        return safe
    if isinstance(item, str):
        return _scrub_pii(item)
    return ""


def _scrub_pii(text: str) -> str:
    import re
    if not text:
        return ""
    original = text
    scrubbed = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    scrubbed = re.sub(
        r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,3}\)?[-.\s]?)?\d{4,5}[-.\s]?\d{4}\b',
        '[PHONE]', scrubbed)
    scrubbed = re.sub(r'https?://\S+', '[URL]', scrubbed)
    scrubbed = re.sub(r'\b(?:linkedin|github)\.com/\S+', '[PROFILE]', scrubbed,
                       flags=re.IGNORECASE)
    if scrubbed != original:
        FairnessMetrics.record_pii_scrub("text_field")
    return scrubbed


def anonymize_candidate_info(candidate: Dict) -> Dict:
    safe_fields = {
        "id", "score", "sourcing_score", "total_experience_years",
        "city", "state", "country", "skills", "position_level",
        "english_level", "current_position", "education_level"
    }
    return {k: v for k, v in candidate.items() if k in safe_fields}
```

**Quem importa este arquivo (verificado):**
| Arquivo consumidor | Import | Uso |
|---|---|---|
| `agents/search.py` (797 linhas) | `from ...fairness import FairnessGuard` | `check_sensitive_filters()`, `should_block_filter()`, `get_filter_warning_message()` — bloqueia filtros discriminatórios e adiciona warning ao resultado |
| `agents/comparison.py` (873 linhas) | `from ...fairness import anonymize_for_llm` | Anonimiza candidatos antes de enviar ao LLM para comparação |
| `agents/report.py` (529 linhas) | `from ...fairness import FairnessGuard, anonymize_for_llm` | Anonimiza candidatos + `add_hiring_probability_disclaimer()` no resultado |

**Quem NÃO importa (verificado — 0 referências a fairness):**
- `domain.py` (586 linhas) — ❌
- `dispatcher.py` — ❌
- `agents/action.py` (728 linhas) — ❌
- `agents/analytics.py` (555 linhas) — ❌
- `agents/base.py` — ❌
- `agents/detail.py` — ❌
- `agents/orchestrator.py` — ❌
- `agents/planner.py` — ❌
- `agents/router.py` — ❌

---

### 1.4 Mapa de Uso Real — Quem Usa Fairness e Quem Não Usa

#### Arquivos que USAM fairness (4 de ~40 arquivos de domínio):

**a) `src/domains/sourced_profile_sourcing/agents/search.py` (L107-208):**
```python
from src.domains.sourced_profile_sourcing.fairness import FairnessGuard

def _advanced_search(self, context, params):
    fairness_warnings = FairnessGuard.check_sensitive_filters(params)
    compliance_warning = FairnessGuard.get_filter_warning_message(fairness_warnings)

    for key in list(params.keys()):
        should_block = FairnessGuard.should_block_filter(
            key,
            allow_exception=context.allow_sensitive_filters,
            justification=context.sensitive_filter_justification,
            user_id=context.user_id
        )
        if should_block:
            logger.warning(f"🚫 Blocked discriminatory filter: {key}")
            return AgentResponse(
                success=False,
                message=f"❌ Filtro por '{key}' bloqueado por políticas de "
                        "igualdade de oportunidades.\n\n"
                        "Se este é um caso de vaga afirmativa, configure "
                        "`allow_sensitive_filters=True` com justificativa.",
                data={}, warnings=["Filtros por atributos protegidos requerem "
                                    "justificativa legal"]
            )
    # ... executa busca ...
    if compliance_warning:
        response.message = f"{compliance_warning}\n\n---\n\n{response.message}"
        response.warnings = (response.warnings or []) + \
            [w.message for w in fairness_warnings]
```

**b) `src/domains/sourced_profile_sourcing/agents/comparison.py` (L272-281, L823-835):**
```python
from src.domains.sourced_profile_sourcing.fairness import anonymize_for_llm

# Na comparação:
anonymized, _ = anonymize_for_llm(candidates_data)
for c in anonymized:
    # ... usa código anônimo (C001, C002) no lugar de nomes
```

**c) `src/domains/sourced_profile_sourcing/agents/report.py` (L9, L233-270):**
```python
from src.domains.sourced_profile_sourcing.fairness import FairnessGuard, anonymize_for_llm

# Na geração de relatórios:
anonymized_top, _ = anonymize_for_llm(top_candidates)
# ... envia candidatos anonimizados ao LLM ...
result = self._parse_json_response(response.content)
return FairnessGuard.add_hiring_probability_disclaimer(result)
```

**d) `src/domains/jobs/actions/matching.py` (completo — 70 linhas):**
```python
from src.domains.jobs.fairness import JobFairnessGuard

class MatchingActions(BaseJobAction):
    def matching_candidates(self, params, context, **kwargs):
        allowed, msg = JobFairnessGuard.check_filters(params)
        if not allowed:
            return DomainResponse(success=False, message=msg)
        # ... executa matching ...
        disclaimer = JobFairnessGuard.get_matching_disclaimer()
        lines = [f"🎯 **{total} candidato(s) com match**", "", table, "", disclaimer]
        return DomainResponse(success=True, message="\n".join(lines), ...)
```

**e) `src/domains/jobs/actions/mutations.py` (L7, L246):**
```python
from src.domains.jobs.fairness import JobFairnessGuard

# No bulk_apply_action:
msg += f"\n\n{JobFairnessGuard.get_bulk_action_disclaimer()}"
```

#### Domínios que NÃO USAM nenhum fairness (6 de 8, verificado por scan completo):

| Domínio | Arquivo principal | Linhas | Referências a fairness | Risco |
|---|---|---|---|---|
| `applies` | `domain.py` (495L) + `react_agent.py` | 0 | 🔴 CRÍTICO — processa candidaturas |
| `evaluation` | `domain.py` (173L) + `nodes.py` + `graph.py` | 0 | 🔴 CRÍTICO — avalia/rankeia candidatos (EU AI Act Art. 6 high-risk) |
| `autonomous` | `domain.py` (139L) + `agent.py` | 0 | 🔴 CRÍTICO — decisões autônomas sem supervisão |
| `insights` | `domain.py` (320L) | 0 | 🟠 ALTO — gera insights que propagam viés |
| `messaging` | `domain.py` (294L) | 0 | 🟠 ALTO — tom/linguagem pode discriminar |
| `scheduling` | `domain.py` (363L) | 0 | 🟠 MÉDIO — "disponibilidade total" é proxy |

**Dado adicional:** Nenhum `domain.py` de nenhum domínio (incluindo jobs e sourcing) importa ou referencia fairness. A fairness existe apenas nas actions/agents específicos.

---

### 1.5 `src/domains/base.py` — Classe Base DomainPrompt (sem fairness)

**Caminho exato:** `src/domains/base.py`
**Leitura:** Direta via GitHub API

```python
class DomainPrompt(ABC):

    @property
    @abstractmethod
    def domain_id(self) -> str: pass

    @property
    @abstractmethod
    def domain_name(self) -> str: pass

    @property
    @abstractmethod
    def description(self) -> str: pass

    @abstractmethod
    def get_allowed_actions(self) -> List[DomainAction]: pass

    @abstractmethod
    def get_system_prompt(self, context: DomainContext) -> str: pass

    @abstractmethod
    def process_intent(self, user_query: str, context: DomainContext) -> Dict[str, Any]: pass

    @abstractmethod
    def execute_action(self, action_id: str, params: Dict[str, Any],
                        context: DomainContext) -> DomainResponse: pass

    def get_suggestions(self, context: DomainContext) -> List[str]:
        return []
```

O `DomainContext` no mesmo arquivo inclui campos de fairness que **existem mas não são usados automaticamente**:
```python
@dataclass
class DomainContext:
    # ... campos regulares ...
    allow_sensitive_filters: bool = False
    sensitive_filter_justification: Optional[str] = None
```

Estes campos existem no contexto, mas **nenhum domain.py os verifica**. Apenas o `search.py` do sourcing consome estes campos.

---

### 1.6 `src/services/pii_filter.py` — Filtro de PII (apenas logging)

**Caminho exato:** `src/services/pii_filter.py`
**Leitura:** Direta via GitHub API

```python
import logging
import re
from typing import List, Tuple

_PII_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'), '[CPF]'),
    (re.compile(r'\b[\w.+-]+@[\w.-]+\.\w{2,}\b'), '[EMAIL]'),
    (re.compile(r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}\b'), '[PHONE]'),
]


def mask_pii(text: str) -> str:
    if not text:
        return text
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class PIIMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            record.msg = mask_pii(str(record.msg))
            record.args = None
        else:
            record.msg = mask_pii(str(record.msg))
        return True


def install_pii_filter():
    root_logger = logging.getLogger()
    if not any(isinstance(f, PIIMaskingFilter) for f in root_logger.filters):
        root_logger.addFilter(PIIMaskingFilter())
```

**Importante:** `mask_pii()` existe como função, mas é usada como `logging.Filter` — NÃO como pré-processamento antes do LLM. PII chega ao LLM externo sem mascaramento. Separado: o `sourced_profile_sourcing/fairness.py` tem sua própria `_scrub_pii()` interna que faz scrubbing de EMAIL, PHONE e URL dentro da função `anonymize_for_llm()`.

---

### 1.7 `src/services/security.py` — Prompt Injection (NÃO é fairness)

**Caminho exato:** `src/services/security.py`
**Leitura:** Direta via GitHub API

Contém 25 patterns de prompt injection (pt-BR e en), `sanitize_input()`, `detect_injection()`, `safe_process_input()`. **Não tem nenhuma referência a fairness, viés ou discriminação.** É segurança contra injeção, não compliance anti-discriminatório.

---

### 1.8 `src/services/audit/` — Audit Callback (NÃO tem fairness)

**Caminho exato:** `src/services/audit/audit_callback.py` (280 linhas)
**Leitura:** Direta via GitHub API

O audit callback registra execuções de LLM (tokens, latência, tool calls), mas **não tem nenhuma referência a fairness**. Não registra bloqueios de filtros discriminatórios, não persiste FairnessMetrics, não tem tabela de audit de fairness.

---

### 1.9 `tests/test_fairness.py` — Suite de Testes de Fairness

**Caminho exato:** `tests/test_fairness.py` (7845 bytes)
**Leitura:** Direta via GitHub API em 31/03/2026

```python
import pytest
from unittest.mock import patch, MagicMock

from src.domains.sourced_profile_sourcing.fairness import (
    FairnessGuard,
    FairnessMetrics,
    anonymize_for_llm,
    _sanitize_analysis,
    _scrub_pii,
    SENSITIVE_FILTER_KEYS
)


class TestAnonymizeForLlm:

    def test_returns_tuple(self):
        candidates = [{"id": 1, "name": "João", "score": 85}]
        result = anonymize_for_llm(candidates)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_anonymized_list_has_candidate_code(self):
        candidates = [{"id": 1, "name": "João", "score": 85}]
        anonymized, _ = anonymize_for_llm(candidates)

        assert anonymized[0]["candidate_code"] == "C001"

    def test_id_mapping_correct(self):
        candidates = [
            {"id": 1, "name": "João"},
            {"id": 2, "name": "Maria"}
        ]
        _, id_mapping = anonymize_for_llm(candidates)

        assert id_mapping["C001"] == "1"
        assert id_mapping["C002"] == "2"

    def test_removes_pii_fields(self):
        candidates = [{
            "id": 1,
            "name": "João Silva",
            "email": "joao@example.com",
            "phone": "11999999999",
            "score": 85,
            "city": "São Paulo"
        }]
        anonymized, _ = anonymize_for_llm(candidates)

        assert "name" not in anonymized[0]
        assert "email" not in anonymized[0]
        assert "phone" not in anonymized[0]
        assert anonymized[0].get("score") == 85
        assert anonymized[0].get("city") == "São Paulo"

    def test_sanitizes_analysis_field(self):
        candidates = [{
            "id": 1,
            "analysis": {
                "highlights": [{"description": "Contato: joao@test.com"}],
                "overall_assessment": "João da Empresa X é bom"
            }
        }]
        anonymized, _ = anonymize_for_llm(
            candidates, fields_to_keep=["analysis"])

        analysis = anonymized[0].get("analysis", {})
        assert "overall_assessment" not in analysis


class TestSanitizeAnalysis:

    def test_removes_unsafe_keys(self):
        analysis = {
            "highlights": [{"description": "test"}],
            "overall_assessment": "João é ótimo",
            "experience_summary": "Trabalhou na Empresa X"
        }
        sanitized = _sanitize_analysis(analysis)

        assert "overall_assessment" not in sanitized
        assert "experience_summary" not in sanitized
        assert "highlights" in sanitized

    def test_keeps_structured_keys(self):
        analysis = {
            "highlights": [{"description": "Good"}],
            "red_flags": [{"severity": "low"}],
            "skills_assessment": {"strong": ["Python"]}
        }
        sanitized = _sanitize_analysis(analysis)

        assert "highlights" in sanitized
        assert "red_flags" in sanitized
        assert "skills_assessment" in sanitized


class TestScrubPii:

    def test_scrubs_email(self):
        text = "Contate em joao.silva@empresa.com para mais info"
        scrubbed = _scrub_pii(text)

        assert "[EMAIL]" in scrubbed
        assert "joao.silva@empresa.com" not in scrubbed

    def test_scrubs_phone(self):
        text = "Ligue para 11 99999-9999 ou +55 11 98888-8888"
        scrubbed = _scrub_pii(text)

        assert "[PHONE]" in scrubbed

    def test_scrubs_url(self):
        text = "Veja em https://linkedin.com/in/joao-silva"
        scrubbed = _scrub_pii(text)

        assert "[URL]" in scrubbed
        assert "linkedin.com/in/joao-silva" not in scrubbed

    def test_preserves_clean_text(self):
        text = "Desenvolvedor Python com 5 anos de experiência"
        scrubbed = _scrub_pii(text)

        assert scrubbed == text


class TestFairnessGuardShouldBlockFilter:

    def test_blocks_race_by_default(self):
        assert FairnessGuard.should_block_filter("race") is True
        assert FairnessGuard.should_block_filter("raca") is True

    def test_blocks_gender_by_default(self):
        assert FairnessGuard.should_block_filter("gender") is True
        assert FairnessGuard.should_block_filter("sexo") is True

    def test_blocks_age_by_default(self):
        assert FairnessGuard.should_block_filter("age") is True
        assert FairnessGuard.should_block_filter("idade") is True

    def test_allows_with_exception_and_justification(self):
        result = FairnessGuard.should_block_filter(
            "gender",
            allow_exception=True,
            justification="Vaga afirmativa para mulheres - Programa Diversidade",
            user_id="user123"
        )
        assert result is False

    def test_blocks_without_justification(self):
        result = FairnessGuard.should_block_filter(
            "gender",
            allow_exception=True,
            justification=None
        )
        assert result is True

    def test_does_not_block_safe_filters(self):
        assert FairnessGuard.should_block_filter("skill") is False
        assert FairnessGuard.should_block_filter("location") is False
        assert FairnessGuard.should_block_filter("experience") is False


class TestFairnessGuardDisclaimers:

    def test_add_discard_disclaimer(self):
        message = "Candidatos para descarte"
        result = FairnessGuard.add_discard_disclaimer(message)

        assert "Aviso de Fairness" in result
        assert "NÃO deve ser usada como decisão final" in result

    def test_add_ranking_disclaimer(self):
        message = "Ranking de candidatos"
        result = FairnessGuard.add_ranking_disclaimer(message)

        assert "sugestão baseada em critérios técnicos" in result

    def test_add_hiring_probability_disclaimer(self):
        analysis = {"hiring_probability": "high"}
        result = FairnessGuard.add_hiring_probability_disclaimer(analysis)

        assert "_disclaimer" in result


class TestFairnessMetrics:

    def test_records_block(self):
        initial = FairnessMetrics._blocked_count
        FairnessMetrics.record_block("gender", "test")

        assert FairnessMetrics._blocked_count == initial + 1

    def test_records_warning(self):
        initial = FairnessMetrics._warnings_count
        FairnessMetrics.record_warning("gender")

        assert FairnessMetrics._warnings_count == initial + 1

    def test_get_stats(self):
        stats = FairnessMetrics.get_stats()

        assert "blocked_count" in stats
        assert "warnings_count" in stats
        assert "pii_scrubbed_count" in stats
        assert "exceptions_allowed" in stats


class TestNoLeakageToPrompt:

    def test_no_name_in_anonymized(self):
        candidates = [
            {"id": 1, "name": "João Silva", "score": 90},
            {"id": 2, "name": "Maria Santos", "score": 85}
        ]
        anonymized, id_mapping = anonymize_for_llm(candidates)

        prompt_content = str(anonymized)

        assert "João" not in prompt_content
        assert "Silva" not in prompt_content
        assert "Maria" not in prompt_content
        assert "Santos" not in prompt_content

        assert "C001" in prompt_content
        assert "C002" in prompt_content

    def test_no_email_in_analysis(self):
        candidates = [{
            "id": 1,
            "analysis": {
                "highlights": [{"description": "Senior dev, email: dev@company.com"}]
            }
        }]
        anonymized, _ = anonymize_for_llm(
            candidates, fields_to_keep=["analysis"])

        prompt_content = str(anonymized)

        assert "dev@company.com" not in prompt_content
        assert "[EMAIL]" in prompt_content

    def test_id_mapping_not_in_prompt(self):
        candidates = [{"id": 123, "name": "Test", "score": 80}]
        anonymized, id_mapping = anonymize_for_llm(candidates)

        assert "123" in str(id_mapping)
        assert "123" not in str(anonymized)
```

**Análise da cobertura de testes:**

| Classe de teste | Nº testes | O que cobre |
|---|---|---|
| `TestAnonymizeForLlm` | 5 | Retorno de tupla, candidato code, ID mapping, remoção de PII, sanitização de analysis |
| `TestSanitizeAnalysis` | 2 | Remoção de chaves inseguras, preservação de chaves estruturadas |
| `TestScrubPii` | 4 | Scrubbing de email, telefone, URL, preservação de texto limpo |
| `TestFairnessGuardShouldBlockFilter` | 4 | Bloqueio de race/gender/age, exceção com justificativa, sem justificativa, filtros seguros |
| `TestFairnessGuardDisclaimers` | 3 | Disclaimers de discard, ranking, hiring_probability |
| `TestFairnessMetrics` | 3 | Registros de block, warning, stats |
| `TestNoLeakageToPrompt` | 3 | Nenhum nome no prompt, nenhum email no prompt, ID mapping não vazado |
| **Total** | **24 testes** | |

**O que NÃO é testado (gaps):**
- `check_sensitive_filters()` — nenhum teste
- `get_filter_warning_message()` — nenhum teste
- `JobFairnessGuard` (do jobs/) — nenhum teste (não é sequer importado)
- Integração com `DomainContext.allow_sensitive_filters` — nenhum teste
- Cenários de texto livre com discriminação — nenhum teste (consistente com a falta de detecção em texto livre)

---

### 1.10 Domínios sem Fairness — Evidência Direta

#### `src/domains/insights/domain.py` (320 linhas)

**Caminho exato:** `src/domains/insights/domain.py`
**Leitura:** Direta via GitHub API
**Referências a fairness/guard/sensitive/bias/discriminat:** 0

Imports (primeiras 16 linhas):
```python
import json
import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.domains.base import DomainAction, DomainContext, DomainResponse, ActionType
from src.domains.insights.actions import InsightsActions
from src.domains.insights.api_client import InsightsAPIClient
from src.domains.insights.memory import InsightsConversationMemory
from src.domains.insights.prompts import build_intent_prompt, build_system_prompt
from src.domains.registry import register_domain
from src.domains.base import DomainPrompt
from src.services.circuit_breaker import circuit_breaker_call, CircuitBreakerOpenError
from src.utils.llm_factory import create_tracked_llm
```

Nenhuma importação de fairness. Nenhuma verificação de bias nos insights gerados. Insights sobre candidatos, vagas e métricas podem conter viés sem detecção.

#### `src/domains/applies/` (sem fairness)

**Estrutura:**
```
src/domains/applies/
├── __init__.py (82b)
├── actions/          (subdir)
├── api_client.py     (10744b)
├── cache.py          (2468b)
├── cards.py          (15493b)
├── config/           (subdir)
├── domain.py         (20525b) — 0 refs a fairness
├── formatters/       (subdir)
├── memory.py         (9948b)
├── prompt_builder/   (subdir)
├── prompts.py        (1387b)
└── react_agent.py    (19320b) — 0 refs a fairness
```

**Nota:** Não existe `dynamic_builder.py` em nenhum domínio do v5 (verificado em jobs/, applies/, services/, e raiz de domains/).

O domínio `applies` processa candidaturas (20525 linhas no domain.py), gerencia kanban, e usa `react_agent.py` (19320 linhas) para decisões — tudo sem qualquer verificação de fairness.

---

### 1.11 Resumo: O que está hardcoded dentro do domínio vs. fora

| Componente | Localização | Dentro de domínio? | Transversal? |
|---|---|---|---|
| `JobFairnessGuard` — 15 filtros bloqueados, PCD context-aware | `jobs/fairness.py` | ✅ Dentro de jobs | ❌ Não é transversal |
| `FairnessGuard` — 18+ filtros, disclaimers, check+block com exceção | `sourced_profile_sourcing/fairness.py` | ✅ Dentro de sourcing | ❌ Não é transversal |
| `FairnessMetrics` — contadores in-memory | `sourced_profile_sourcing/fairness.py` | ✅ Dentro de sourcing | ❌ Não é transversal |
| `anonymize_for_llm()` — anonimização de candidatos | `sourced_profile_sourcing/fairness.py` | ✅ Dentro de sourcing | ❌ Não é transversal |
| `_scrub_pii()` — scrubbing de EMAIL/PHONE/URL | `sourced_profile_sourcing/fairness.py` | ✅ Dentro de sourcing | ❌ Não é transversal |
| `DomainContext.allow_sensitive_filters` | `base.py` | ✅ Classe base | ⚠️ Disponível mas não consumido automaticamente |
| `pii_filter.py` — mask_pii() para logging | `services/pii_filter.py` | ❌ Serviço compartilhado | ⚠️ Apenas logging, não pré-LLM |
| `security.py` — prompt injection guard | `services/security.py` | ❌ Serviço compartilhado | ✅ Transversal (mas não é fairness) |
| `audit_callback.py` — audit de execução | `services/audit/` | ❌ Serviço compartilhado | ✅ Transversal (mas sem fairness) |

**Conclusão:** A infraestrutura compartilhada (`src/services/`) **não tem fairness**. Fairness é implementado separadamente dentro de cada domínio que optou por tê-lo. 6/8 domínios não optaram.

---

## 2. Inventário Completo — FairnessGuard LIA/Replit

### 2.1 Arquitetura de 3 Camadas

**Arquivo central:** `lia-agent-system/app/shared/compliance/fairness_guard.py` (806 linhas)
**Leitura:** Direta do filesystem Replit

#### Layer 1 — Detecção Explícita (Regex)

13 categorias discriminatórias com regex multi-padrão e mensagem educativa com citação legal:

| Categoria | Qtd Patterns | Base Legal |
|---|---|---|
| `genero` | 8 | Art. 5º CLT, LGPD |
| `raca_etnia` | 8 | CF Art. 5º, Lei 7.716/89 |
| `idade` | 13 | Lei 10.741/03 (Estatuto do Idoso) |
| `religiao` | 3 | CF Art. 5º, VI |
| `orientacao_sexual` | 3 | ADO 26 (STF) |
| `estado_civil` | 3 | CLT |
| `deficiencia` | 8 | Lei 8.213/91 (Cotas), Lei 13.146/15 |
| `maternidade_paternidade` | 13 | CLT Art. 373-A, Lei 9.029/95 |
| `nacionalidade` | 3 | CF Art. 5º |
| `antecedentes_criminais` | 7 | CNJ Resolução 65/08, Lei 7.210/84 |
| `saude_doenca` | 8 | Lei 9.029/95, Lei 9.313/96 |
| `filiacao_sindical` | 6 | CLT Art. 543, CF Art. 8º |
| `aparencia_fisica` | 10 | Lei 9.029/95 |
| **Total** | **~96 patterns** | |

Método `check()` central (lido de `fairness_guard.py`, linhas 372-422):

```python
class FairnessGuard:
    def __init__(self):
        _ensure_compiled()

    def check(self, query: str) -> FairnessCheckResult:
        if not query or not query.strip():
            return FairnessCheckResult(is_blocked=False, original_query=query)
        query_lower = query.lower().strip()
        query_normalized = _normalize_text(query_lower)
        blocked_terms = []
        detected_category = None
        max_confidence = 0.0
        for category, patterns in _COMPILED_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(query_lower)
                if not match:
                    match = pattern.search(query_normalized)
                if match:
                    blocked_terms.append(match.group())
                    if not detected_category:
                        detected_category = category
                    confidence = min(0.95, 0.7 + len(match.group()) * 0.02)
                    max_confidence = max(max_confidence, confidence)
        soft_warnings = self.check_implicit_bias(query)
        if blocked_terms and detected_category:
            educational_message = DISCRIMINATORY_CATEGORIES[detected_category]["message"]
            return FairnessCheckResult(
                is_blocked=True, blocked_terms=blocked_terms,
                category=detected_category,
                educational_message=educational_message,
                original_query=query, confidence=max_confidence,
                soft_warnings=soft_warnings,
            )
        return FairnessCheckResult(is_blocked=False, original_query=query,
                                   soft_warnings=soft_warnings)
```

#### Layer 2 — Detecção Implícita (Léxico)

`IMPLICIT_BIAS_TERMS` — 23+ termos de viés implícito: "universidades de primeira linha", "boa aparência", "disponibilidade total", "sem adaptações", "perfil adequado", "energia jovem", etc.

#### Layer 3 — Análise Semântica por LLM

`check_with_layer3()` — Claude Haiku com feature flag `FAIRNESS_LAYER3_ENABLED`, cache Redis 1h TTL, ativado para: rejection, shortlist, wsi_score, policy_save, bulk_rejection, sourcing_search, jd_import, pipeline_move.

### 2.2 Middleware, Audit, API, Mixin

| Componente | Arquivo | Linhas | Função |
|---|---|---|---|
| Middleware | `fairness_guard_middleware.py` | 196 | `check_fairness()`, `check_fairness_async()`, `check_rejection_reason()` |
| Audit Log | `fairness_audit.py` | 67 | Tabela PostgreSQL com UUID, SHA-256 hash, JSONB, timestamps |
| API Reports | `fairness_reports.py` | 321 | 4 endpoints: summary, trend, audit logs, export CSV/JSON |
| Agent Mixin | `enhanced_agent_mixin.py` | 401 | `_fairness_pre_check()` automático em todos os agentes |

**Cobertura:** 11/11 agentes + MainOrchestrator via herança obrigatória (`EnhancedAgentMixin`)

### 2.3 Diferença Fundamental de Design

```python
# LIA — compliance automático por herança (custo: 2 linhas)
class NovoAgente(LangGraphReActBase, EnhancedAgentMixin):
    def __init__(self):
        super().__init__()
        self._setup_enhanced(domain="novo")
        # FairnessGuard, PII, Audit: automáticos

# v5 — compliance por disciplina do desenvolvedor (custo: manual)
class NovoDominio(DomainPrompt):
    def process_intent(self, query, context):
        return self._classify(query, context)  # sem fairness
    # Nada na arquitetura obriga — apenas memória do dev
```

---

## 3. Tabela Comparativa — Dimensão por Dimensão

| # | Capacidade | v5 | LIA | Gap |
|---|---|---|---|---|
| 01 | **Categorias protegidas** | 8 (SensitiveAttribute) | 13 (DISCRIMINATORY_CATEGORIES) | ⚠️ v5 falta: antecedentes, saúde, sindical, aparência, maternidade |
| 02 | **Detecção em texto livre (regex)** | ❌ Apenas nomes de campo de filtro | ✅ ~96 patterns regex | ❌ CRÍTICO |
| 03 | **Detecção de viés implícito (L2)** | ❌ Não existe | ✅ 23+ termos | ❌ CRÍTICO |
| 04 | **Análise semântica LLM (L3)** | ❌ | ✅ Claude Haiku + cache | ❌ |
| 05 | **Bloqueio de filtros estruturados** | ✅ `BLOCKED_FILTERS` + `SENSITIVE_FILTER_KEYS` | ✅ Via L1 regex + middleware | ✅ |
| 06 | **Anonimização pré-LLM** | ✅ `anonymize_for_llm()` em sourcing (comparison + report) | ✅ Blind evaluation em todos os agentes | ⚠️ v5 tem mas só em sourcing |
| 07 | **PII scrubbing** | ⚠️ `_scrub_pii()` interno ao fairness de sourcing + `pii_filter.py` (logging only) | ✅ `pii_masking.py` pré-LLM | ⚠️ |
| 08 | **Disclaimers** | ✅ 3 disclaimers tipados (DISCARD, RANKING, HIRING_PROBABILITY) + 2 (MATCHING, BULK_ACTION) | ✅ Educational messages por categoria com base legal | ✅ v5 tem disclaimers bem estruturados |
| 09 | **Audit log persistente** | ❌ `FairnessMetrics` in-memory (perdidos no restart) | ✅ `fairness_audit_log` PostgreSQL | ❌ CRÍTICO |
| 10 | **Métricas/Observabilidade** | ❌ Contadores in-memory + logger.warning | ✅ Prometheus + Grafana | ❌ |
| 11 | **Middleware reutilizável** | ❌ Cada domínio reimplementa diferente | ✅ `fairness_guard_middleware.py` | ❌ |
| 12 | **Mecanismo de exceção com justificativa** | ✅ `allow_sensitive_filters` + `justification` + `record_exception_allowed()` | ⚠️ Via feature flag L3 | ✅ v5 tem mecanismo mais explícito |
| 13 | **PCD context-aware** | ✅ `PCD_CONTEXT_REQUIRED` — só permite filtro PCD se `disabilities=true` na vaga | ⚠️ Reconhece Lei 8.213/91 mas sem context check | ✅ v5 tem regra inteligente |
| 14 | **Cobertura de domínios** | ⚠️ 4 actions/agents em 2 domínios (de 8 domínios) | ✅ 11/11 agentes + Orchestrator | ❌ CRÍTICO |
| 15 | **Interceptação pré-LLM** | ❌ Verifica filtros, não texto do recrutador | ✅ Intercepta antes de qualquer processamento | ❌ CRÍTICO |
| 16 | **Mensagens educativas com base legal** | ⚠️ Mensagens genéricas ("políticas de diversidade") | ✅ Citação de lei específica por categoria | ❌ CRÍTICO |
| 17 | **API de relatórios** | ❌ | ✅ 4 endpoints | ❌ |
| 18 | **Normalização Unicode** | ❌ | ✅ NFD | ❌ |
| 19 | **Red team testing** | ❌ | ✅ `test_red_team_fairness.py` | ❌ |
| 20 | **Bias Audit (Four-Fifths Rule)** | ❌ | ✅ 4 dimensões | ❌ |
| 21 | **Learning batch validation** | ❌ | ✅ 32 campos protegidos | ❌ |
| 22 | **Sector-aware** | ❌ | ✅ 6 setores | ❌ |

---

## 4. Análise de Riscos Regulatórios do v5

### 4.1 Ausência de Detecção em Texto Livre

**Cenário:** Recrutador digita "quero candidatos jovens de até 30 anos, sem filhos, de boa aparência"

| Sistema | Resultado |
|---|---|
| **v5** | ❌ Mensagem passa sem detecção. O `FairnessGuard` do v5 verifica `params["gender"]`, `params["age"]` etc. — nomes de campo de dicionário. Texto livre do recrutador não é interceptado em nenhum ponto. |
| **LIA** | ✅ L1 detecta "até 30 anos" (idade), "sem filhos" (maternidade), "boa aparência" (L2 implícito). Três bloqueios com mensagens educativas. |

### 4.2 Inconsistência Cross-Domínio (verificado por scan GitHub)

```
Recrutador digita: "Só quero candidatas mulheres para essa vaga"

→ Domínio jobs/matching:    ✅ JobFairnessGuard.check_filters() bloqueia se
                            "gender" vier como campo de filtro
→ Domínio jobs/query:       ❌ Sem fairness — query textual passa direto
→ Domínio sourcing/search:  ✅ FairnessGuard.should_block_filter() bloqueia
                            se "gender" vier como parâmetro
→ Domínio evaluation:       ❌ Sem fairness — avaliação com viés
→ Domínio autonomous:       ❌ Sem fairness — decisão autônoma executada
→ Domínio applies:          ❌ Sem fairness — candidaturas filtradas com viés
→ Domínio insights:         ❌ Sem fairness — insight enviesado gerado
→ Domínio messaging:        ❌ Sem fairness — mensagem com viés
→ Domínio scheduling:       ❌ Sem fairness

Resultado: Fairness funciona APENAS para filtros estruturados em 2 domínios.
Texto livre e 6 domínios inteiros estão desprotegidos.
```

### 4.3 Risco por Ausência de Audit Trail

| Requisito | v5 | LIA |
|---|---|---|
| **EU AI Act Art. 14** | ❌ `FairnessMetrics` in-memory, perdidos no restart | ✅ PostgreSQL com SHA-256 |
| **LGPD Art. 20** | ❌ Sem registro recuperável | ✅ Audit trail via API |
| **SOX** | ❌ Sem persistência | ✅ Relatórios exportáveis |

### 4.4 Risco de Exposição

| Cenário | v5 Protegido? | LIA Protegido? |
|---|---|---|
| Recrutador pede "candidatas mulheres" via chat | ❌ (texto livre não interceptado) | ✅ |
| Filtro por `gender` em busca de sourcing | ✅ (should_block_filter) | ✅ |
| Viés "boa aparência" em avaliação | ❌ (evaluation sem fairness) | ✅ |
| Exclusão de PCDs por proxy ("sem adaptações") | ❌ (sem L2 implícito) | ✅ |
| Auditoria regulatória pede logs de fairness | ❌ (in-memory perdidos) | ✅ |
| Matching com filtro PCD sem vaga afirmativa | ✅ (PCD_CONTEXT_REQUIRED) | ⚠️ |

---

## 5. Mapa de Dispersão Arquitetural

### 5.1 v5 — Modelo Descentralizado (verificado por scan GitHub)

```
src/
├── domains/
│   ├── base.py                    DomainPrompt — sem fairness, mas tem
│   │                              allow_sensitive_filters no DomainContext
│   ├── jobs/
│   │   ├── fairness.py            ✅ JobFairnessGuard (15 filtros, PCD context, 2 disclaimers)
│   │   ├── domain.py              ❌ NÃO importa fairness.py (533L, 0 refs)
│   │   ├── dispatcher.py          ❌ NÃO importa fairness.py
│   │   └── actions/
│   │       ├── matching.py        ✅ check_filters() + matching disclaimer
│   │       ├── mutations.py       ✅ bulk_action_disclaimer()
│   │       ├── analytics.py       ❌ NÃO importa fairness
│   │       ├── query.py           ❌ NÃO importa fairness
│   │       ├── suggestions.py     ❌ NÃO importa fairness
│   │       └── conversational.py  ❌ NÃO importa fairness
│   ├── sourced_profile_sourcing/
│   │   ├── fairness.py            ✅ FairnessGuard + Metrics + anonymize (271L)
│   │   ├── domain.py              ❌ NÃO importa fairness.py (586L, 0 refs)
│   │   ├── dispatcher.py          ❌ NÃO importa fairness.py
│   │   └── agents/
│   │       ├── search.py          ✅ check_sensitive_filters + should_block_filter (797L)
│   │       ├── comparison.py      ✅ anonymize_for_llm (873L)
│   │       ├── report.py          ✅ anonymize + hiring_probability_disclaimer (529L)
│   │       ├── action.py          ❌ NÃO importa fairness (728L)
│   │       ├── analytics.py       ❌ NÃO importa fairness (555L)
│   │       ├── base.py            ❌ NÃO importa fairness
│   │       ├── detail.py          ❌ NÃO importa fairness
│   │       ├── orchestrator.py    ❌ NÃO importa fairness
│   │       ├── planner.py         ❌ NÃO importa fairness
│   │       └── router.py          ❌ NÃO importa fairness
│   ├── applies/                   ❌ 0 refs a fairness em 2 arquivos (495+L)
│   ├── evaluation/                ❌ 0 refs a fairness em 7 arquivos (high-risk!)
│   ├── autonomous/                ❌ 0 refs a fairness em 12 arquivos
│   ├── insights/                  ❌ 0 refs a fairness em 6 arquivos
│   ├── messaging/                 ❌ 0 refs a fairness em 7 arquivos
│   └── scheduling/                ❌ 0 refs a fairness em 8 arquivos
├── services/
│   ├── pii_filter.py              ⚠️ mask_pii() para logging (35L)
│   ├── security.py                ⚠️ prompt injection (não fairness)
│   └── audit/                     ⚠️ audit de execução (não fairness)
└── (sem services/fairness)        ❌ NÃO existe serviço compartilhado de fairness
```

### 5.2 LIA — Modelo Centralizado

```
app/shared/compliance/
├── fairness_guard.py            ✅ 806L — fonte única, 3 layers, 13 categorias
├── fairness_guard_middleware.py  ✅ 196L — middleware reutilizável
└── guardrail_repository.py      ✅ Guardrails em banco (global→tenant→domínio)

libs/models/lia_models/
└── fairness_audit.py            ✅ 67L — audit log PostgreSQL

app/api/v1/
└── fairness_reports.py          ✅ 321L — 4 endpoints de relatório

libs/agents-core/
└── enhanced_agent_mixin.py      ✅ 401L — _fairness_pre_check() automático

Cobertura: 11/11 agentes + MainOrchestrator (100%)
```

---

## 6. Recomendações Priorizadas

### P0 — Bloqueadores Regulatórios (0-2 semanas)

| # | Recomendação | Esforço | Justificativa |
|---|---|---|---|
| P0-1 | **Criar `src/services/compliance/fairness_guard.py` centralizado** com detecção em texto livre (regex) — copiar ~96 patterns da LIA com 13 categorias | 16h | Texto livre do recrutador é o principal vetor de viés e não é interceptado |
| P0-2 | **Integrar FairnessGuard no `DomainPrompt.process_intent()`** em `base.py` — wrapper pré-LLM que cobre 8/8 domínios com 1 ponto de integração | 2h | 6/8 domínios sem proteção |
| P0-3 | **Adicionar 5 categorias faltantes** — antecedentes_criminais, saude_doenca, filiacao_sindical, aparencia_fisica, maternidade_paternidade | 4h | Risco regulatório direto |
| P0-4 | **Persistir FairnessMetrics** — criar tabela `fairness_audit_log` (copiar schema LIA) | 4h | EU AI Act Art. 14, LGPD Art. 20 |

### P1 — Compliance Avançado (2-4 semanas)

| # | Recomendação | Esforço |
|---|---|---|
| P1-1 | **Layer 2 (viés implícito)** — copiar `IMPLICIT_BIAS_TERMS` da LIA (23+ termos) | 4h |
| P1-2 | **Mensagens educativas com base legal** — substituir "políticas de diversidade" por citação legislativa | 8h |
| P1-3 | **Middleware centralizado** — `check_fairness()` reutilizável | 4h |
| P1-4 | **Suite de bias regression em CI** — 20+ queries parametrizadas | 8h |
| P1-5 | **FairnessGuard nos agents sem proteção** — action.py, analytics.py, detail.py do sourcing | 4h |

### P2 — Paridade Funcional (4-8 semanas)

| # | Recomendação | Esforço |
|---|---|---|
| P2-1 | **Layer 3 (LLM semântico)** — Haiku para ações high-risk | 16h |
| P2-2 | **Estender `anonymize_for_llm()`** para todos os domínios (não só sourcing) | 4h |
| P2-3 | **API de relatórios de compliance** | 16h |
| P2-4 | **Métricas Prometheus** | 4h |
| P2-5 | **Expandir `pii_filter.py`** para pré-LLM (não só logging) | 4h |

### P3 — Excelência (8+ semanas)

| # | Recomendação | Esforço |
|---|---|---|
| P3-1 | **Bias Audit (Four-Fifths Rule)** | 24h |
| P3-2 | **Learning batch validation** | 8h |
| P3-3 | **Red team testing framework** | 16h |

### Recomendações da LIA ← v5

| # | O que a LIA pode incorporar do v5 | Prioridade |
|---|---|---|
| R1 | **Mecanismo de exceção com justificativa** — `allow_sensitive_filters` + `sensitive_filter_justification` + `record_exception_allowed()` com log de timestamp/user/filter | P1 |
| R2 | **PCD context-aware** — `PCD_CONTEXT_REQUIRED` que verifica se a vaga tem `disabilities=true` antes de permitir filtro PCD (regra inteligente) | P1 |
| R3 | **Disclaimers tipados** — DISCARD, RANKING, HIRING_PROBABILITY, MATCHING, BULK_ACTION como enum | P2 |
| R4 | **`anonymize_for_llm()` com `_sanitize_analysis()`** — scrubbing de PII dentro de analysis (highlights, red_flags) com truncation a 3 items | P2 |

---

## 7. Conclusão

O v5 tem funcionalidades de fairness **mais robustas do que o esperado** — a `anonymize_for_llm()` com scrubbing de PII e sanitização de análises é sofisticada, o mecanismo de exceção com justificativa é bem desenhado, e o `PCD_CONTEXT_REQUIRED` é uma regra inteligente que a LIA não tem equivalente. Os 5 disclaimers tipados são claros e úteis.

No entanto, **o gap fundamental permanece**: fairness no v5 é uma funcionalidade opt-in implementada em 4 actions/agents específicos de 2 domínios — não é garantia arquitetural. **Nenhum `domain.py`** importa ou consome fairness, nenhum `dispatcher.py` verifica viés, e **6 de 8 domínios** (incluindo evaluation e autonomous — os de maior risco) não têm nenhuma proteção.

**O risco mais crítico:** Um recrutador digita texto discriminatório e o v5 não intercepta em nenhum ponto. A proteção existe apenas para filtros estruturados (quando o recrutador explicitamente passa `params["gender"]`), não para linguagem natural. Na LIA, a mesma frase é interceptada por ~96 patterns regex + 23 termos de viés implícito + análise semântica por LLM.

A recomendação P0-2 (integrar FairnessGuard no `DomainPrompt.process_intent()` de `base.py`) resolve a cobertura de 8/8 domínios com 1 mudança.

---

## Apêndice A — Proveniência dos Dados

| Arquivo | Método de Leitura | Data | Hash/Evidência |
|---|---|---|---|
| `src/domains/jobs/fairness.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | Conteúdo integral reproduzido na seção 1.2 |
| `src/domains/sourced_profile_sourcing/fairness.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | Conteúdo integral reproduzido na seção 1.3 |
| `src/domains/base.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | DomainPrompt + DomainContext reproduzidos na seção 1.5 |
| `src/services/pii_filter.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | Conteúdo integral reproduzido na seção 1.6 |
| `src/services/security.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | Primeiras 2000 chars lidos, resumido na seção 1.7 |
| `src/services/audit/audit_callback.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | 280L, scan por "fairness" = 0 resultados |
| `src/domains/sourced_profile_sourcing/agents/search.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | 797L, fairness block L107-208 reproduzido |
| `src/domains/sourced_profile_sourcing/agents/comparison.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | 873L, anonymize block L272-281 reproduzido |
| `src/domains/sourced_profile_sourcing/agents/report.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | 529L, fairness imports + disclaimer reproduzidos |
| `src/domains/jobs/actions/matching.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | Conteúdo integral (70L) reproduzido na seção 1.4d |
| `src/domains/jobs/actions/mutations.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | Fairness block L7+L246 reproduzido |
| `tests/test_fairness.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | Conteúdo integral (7845 bytes, 24 testes) reproduzido na seção 1.9 |
| `src/domains/insights/domain.py` | GitHub API via ReplitConnectors proxy | 31/03/2026 | 320L, imports + scan por fairness = 0 refs, seção 1.10 |
| `src/domains/applies/` (estrutura completa) | GitHub API via ReplitConnectors proxy | 31/03/2026 | 11 arquivos/dirs, 0 refs a fairness, seção 1.10 |
| Todos os 8 `domain.py` | GitHub API — scan por "fairness\|guard\|sensitive\|disclaimer" | 31/03/2026 | 0 resultados em cada um |
| Todos os agents do sourcing (10 arquivos) | GitHub API — scan por "fairness\|guard\|anonymize\|disclaimer\|sensitive" | 31/03/2026 | Apenas search/comparison/report têm refs |
| `lia-agent-system/app/shared/compliance/fairness_guard.py` | Leitura direta filesystem Replit | 31/03/2026 | 806 linhas |
| `lia-agent-system/app/shared/compliance/fairness_guard_middleware.py` | Leitura direta filesystem Replit | 31/03/2026 | 196 linhas |
| `lia-agent-system/libs/models/lia_models/fairness_audit.py` | Leitura direta filesystem Replit | 31/03/2026 | 67 linhas |
| `lia-agent-system/app/api/v1/fairness_reports.py` | Leitura direta filesystem Replit | 31/03/2026 | 321 linhas |
| `lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` | Leitura direta filesystem Replit | 31/03/2026 | 401 linhas |

---

## Apêndice B — Checklist de Requisitos do Task

| # | Requisito | Seção | Status |
|---|---|---|---|
| 1 | Inventário v5 com conteúdo integral dos arquivos de fairness | 1.2 (jobs/fairness.py integral), 1.3 (sourcing/fairness.py integral), 1.9 (tests/test_fairness.py integral) | ✅ |
| 2 | Caminhos exatos dos arquivos v5 | Todas as seções do cap. 1 (1.1–1.11) | ✅ |
| 3 | Inventário LIA/Replit FairnessGuard estruturado | Cap. 2 (6 subsections) | ✅ |
| 4 | Tabela comparativa dimensional | Cap. 3 (22 dimensões) | ✅ |
| 5 | Análise de riscos regulatórios | Cap. 4 (4 subsections) | ✅ |
| 6 | Mapa de dispersão arquitetural | Cap. 5 (árvore completa com status ✅/❌ por arquivo) | ✅ |
| 7 | Recomendações priorizadas P0-P3 | Cap. 6 (P0: 4 items, P1: 5, P2: 5, P3: 3, R: 4) | ✅ |
| 8 | Quais domínios usam fairness.py | 1.4 (mapa detalhado com evidência de imports) | ✅ |
| 9 | O que está hardcoded vs transversal | 1.11 (tabela componente-por-componente) | ✅ |
| 10 | Se existe infra compartilhada de fairness | 1.1 e 1.11 (não existe em services/) | ✅ |
| 11 | Proveniência de dados verificável | Apêndice A (21 arquivos/grupos documentados) | ✅ |
| 12 | Testes de fairness com conteúdo integral | 1.9 (test_fairness.py integral, 24 testes, análise de gaps) | ✅ |
| 13 | Domínios sem fairness com evidência | 1.10 (insights/domain.py imports, applies/ estrutura completa) | ✅ |
| 14 | Verificação de dynamic_builder | 1.10 (não existe em nenhum domínio do v5) | ✅ |
