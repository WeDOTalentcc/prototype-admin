"""
Schema canonical do ITEM de pergunta de elegibilidade (snapshot na vaga).

Epico Elegibilidade 2026-06-03 (canonical-fix). Fonte unica de verdade do shape
gravado em JobVacancy.eligibility_questions (JSONB) e consumido pelo produtor
unico EligibilityVerificationService.

Reconcilia 4 shapes divergentes historicos:
  - Wizard EligibilityPanel:       {question, required_answer: "yes"|"no"}
  - Edicao de vaga (job.types.ts): {question, type, disqualify_on_fail, expected_answer, order}
  - Catalogo Settings (template):  {question, type, category, eliminatory, eliminatoryAnswer}
  - Extractor legado:              {question_text|text, is_eliminatory, category}

Normalizacao via model_validator(mode="before") — UNICO ponto de traducao.
Qualquer novo produtor de elegibilidade DEVE gravar/ler atraves deste schema.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Variantes "sim" para mapear required_answer (wizard) -> expected_answer canonico
_YES_VARIANTS = {"sim", "yes", "s", "y", "1", "true", "positivo"}


def infer_category(question_text: str) -> str:
    """Infere a categoria (para template de reconsideracao) a partir do texto.

    Espelha EligibilityVerificationService._infer_category_from_question para
    manter UM unico criterio de inferencia (canonical-fix).
    """
    t = (question_text or "").lower()
    if any(w in t for w in ["presencial", "remoto", "hibrido", "hibrida", "modelo"]):
        return "work_model"
    if any(
        w in t
        for w in ["cidade", "estado", "localizacao", "regiao", "mudanca", "deslocamento"]
    ):
        return "location"
    if any(w in t for w in ["inicio", "disponibilidade", "quando", "imediato"]):
        return "availability"
    if any(
        w in t
        for w in ["cnh", "habilitacao", "certificacao", "ingles", "idioma", "diploma"]
    ):
        return "legal"
    return "default"


class EligibilityQuestionItem(BaseModel):
    """Item canonical de pergunta de elegibilidade (snapshot na vaga).

    extra='forbid' no resultado: o model_validator(before) consome todos os
    aliases legados e devolve apenas as chaves canonicas, entao forbid nao barra
    entradas legadas — barra apenas chaves desconhecidas no shape ja canonico.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = ""
    question: str = Field(..., min_length=1, max_length=1000)
    question_type: str = "yes_no"
    options: list[str] | None = None
    is_eliminatory: bool = True
    expected_answer: str | None = None
    category: str = "default"
    order: int = 0

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        out: dict[str, Any] = {}

        out["id"] = str(d.get("id", d.get("legacy_id", "")) or "")

        # question: question | question_text | text
        out["question"] = str(
            d.get("question") or d.get("question_text") or d.get("text") or ""
        ).strip()

        # question_type: question_type | type
        out["question_type"] = d.get("question_type") or d.get("type") or "yes_no"

        out["options"] = d.get("options")

        # is_eliminatory: is_eliminatory | eliminatory | disqualify_on_fail | required
        # default True — por definicao uma pergunta de ELEGIBILIDADE e eliminatoria
        elim = d.get("is_eliminatory")
        if elim is None:
            elim = d.get("eliminatory")
        if elim is None:
            elim = d.get("disqualify_on_fail")
        if elim is None:
            elim = d.get("required")
        out["is_eliminatory"] = bool(elim) if elim is not None else True

        # expected_answer: expected_answer | eliminatoryAnswer | required_answer(yes/no)
        exp: Any = d.get("expected_answer")
        if exp is None:
            exp = d.get("eliminatoryAnswer")
        if exp is None and "required_answer" in d:
            ra = str(d.get("required_answer") or "").strip().lower()
            if ra:
                exp = "Sim" if ra in _YES_VARIANTS else "Nao"
        if isinstance(exp, bool):
            exp = "Sim" if exp else "Nao"
        out["expected_answer"] = exp

        # category: explicita | inferida do texto
        cat = d.get("category")
        out["category"] = cat if cat else infer_category(out["question"])

        # order
        try:
            out["order"] = int(d.get("order", 0) or 0)
        except (TypeError, ValueError):
            out["order"] = 0

        return out
