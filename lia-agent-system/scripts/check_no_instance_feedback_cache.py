#!/usr/bin/env python3
"""Sensor P1-3: o boost de feedback de busca DEVE permanecer stateless + tenant-safe.

Contexto: lia_score_service e singleton de modulo COMPARTILHADO entre tenants.
Guardar feedback em estado de instancia (self._search_feedback_cache) vaza
feedback entre empresas sob concorrencia async (LGPD/multi-tenancy). O fix
canonico (P1-3) usa feedback_map como ARGUMENTO explicito + loader stateless
load_search_feedback escopado por company_id.

Falha se:
  (1) self._search_feedback_cache reaparecer (estado de instancia), ou
  (2) load_search_feedback nao filtrar por SearchFeedback.company_id.

Uso: python3 scripts/check_no_instance_feedback_cache.py [--warn-only]
"""
import re
import sys

TARGET = "app/domains/cv_screening/services/lia_score_service.py"


def main() -> int:
    try:
        src = open(TARGET, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"SKIP: {TARGET} nao encontrado (rode a partir de lia-agent-system/)")
        return 0

    violations = []

    if "self._search_feedback_cache" in src:
        violations.append(
            "self._search_feedback_cache reintroduzido em lia_score_service.py. "
            "O service e singleton compartilhado entre tenants -> estado de instancia "
            "VAZA feedback cross-tenant. FIX: nao guardar feedback em self.*; passe "
            "feedback_map como argumento explicito e use load_search_feedback (stateless)."
        )

    m = re.search(r"async def load_search_feedback\(.*?\n    (?:async )?def ", src, re.S)
    body = m.group(0) if m else ""
    if not body:
        violations.append(
            "load_search_feedback ausente em lia_score_service.py. O loader stateless "
            "escopado por company_id e o produtor unico do feedback_map (P1-3)."
        )
    elif "SearchFeedback.company_id" not in body:
        violations.append(
            "load_search_feedback NAO filtra por SearchFeedback.company_id -> multi-tenancy "
            "fail-open (a app conecta como superuser, RLS inerte; o WHERE company_id e a "
            "barreira real). FIX: adicione SearchFeedback.company_id == str(company_id) ao WHERE."
        )

    if violations:
        print("FAIL check_no_instance_feedback_cache:")
        for v in violations:
            print("  - " + v)
        return 0 if "--warn-only" in sys.argv else 1

    print("OK: feedback boost stateless + escopado por company_id (P1-3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
