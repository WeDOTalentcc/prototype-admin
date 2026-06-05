"""seed_session - build a JobCreationSeed from a chosen source and merge it
into a fresh wizard initial_state.

Thin async seam over the canonical producer (``JobSeedBuilderService``) + the
pure mapper (``apply_seed_to_state``). Exists so the wizard new-session entry
(``WizardSessionService._build_state``) can be seeded from a template/vacancy
without inlining producer calls into the ~1700-line session service, and so the
behaviour is unit-testable in isolation (PR-A5b).

Canonical rules honoured:
  - Reuse the single producer + the single mapper. No reimplementation.
  - No fabrication: if the source is unknown/unwired, the state is returned
    unchanged (a log line records the no-op).
  - Fail soft on tenant/lookup errors (ValueError/PermissionError): log a
    warning and proceed without a seed — a bad source must NOT crash the
    wizard session. State is left clean (no fabricated seed_error marker).
"""
from __future__ import annotations

import logging
from typing import Any

from app.domains.job_creation.helpers.seed_apply import apply_seed_to_state
from app.domains.job_creation.services.job_seed_builder_service import (
    JobSeedBuilderService,
)

logger = logging.getLogger(__name__)


async def seed_initial_state(
    initial_state: dict,
    seed_source: dict | None,
    company_id: str,
    db,
) -> dict:
    """If ``seed_source`` is present, build the seed via the canonical producer
    and merge it into ``initial_state`` (in place) via ``apply_seed_to_state``.

    Returns ``initial_state``. Fails loud-but-soft: producer errors are logged
    and the wizard proceeds without a seed (no crash, no fabrication). Only the
    ``template`` source type is wired today; ``vacancy`` is a later PR.
    """
    if not seed_source:
        return initial_state

    stype = seed_source.get("type")
    sid = seed_source.get("id")

    if not sid:
        logger.info("seed source missing id (type=%s) — skipping seed", stype)
        return initial_state

    if stype not in ("template", "vacancy"):
        # Tipo desconhecido — nao fabricar. Segue sem seed (no-op logado).
        logger.info("seed source type %s not wired — skipping seed", stype)
        return initial_state

    try:
        builder = JobSeedBuilderService(db)
        if stype == "vacancy":
            seed = await builder.build_seed_from_vacancy(sid, company_id)
        else:
            seed = await builder.build_seed_from_template(sid, company_id)
    except (ValueError, PermissionError) as exc:
        # Unknown template / cross-tenant template: fail soft, do not crash the
        # session. The recruiter just proceeds without a seed.
        logger.warning(
            "seed build failed for template id=%s company=%s (%s: %s) — "
            "proceeding without seed",
            sid,
            company_id,
            type(exc).__name__,
            exc,
        )
        return initial_state

    apply_seed_to_state(initial_state, seed)
    logger.info(
        "seeded initial_state from template id=%s (filled=%s/%s)",
        sid,
        getattr(seed, "coverage_filled", "?"),
        getattr(seed, "coverage_total", "?"),
    )
    return initial_state
