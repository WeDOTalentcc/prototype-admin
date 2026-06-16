"""Sensor (audit P2-1/#12 2026-06-05): proibe DUAS classes 'JdEnrichmentService'.

Existiam duas homonimas — job_creation/services/jd_enrichment.py (sync, F1 WSI,
CANONICA) e job_management/services/jd_enrichment_service.py (async, enrich+persist).
Mesmo nome = import confuso + drift de completeness/quality entre as duas. A
job_management foi renomeada para JobManagementJdEnrichmentService. Este sensor
impede a reintroducao do homonimo.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../lia-agent-system
_CLASS_RE = re.compile(r"^class JdEnrichmentService\b", re.MULTILINE)


def test_no_homonym_jd_enrichment_service():
    hits = []
    for p in (ROOT / "app").rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if _CLASS_RE.search(txt):
            hits.append(str(p.relative_to(ROOT)))
    assert len(hits) <= 1, (
        f"Mais de uma classe 'JdEnrichmentService' (homonimo): {hits}. "
        "O canonico e app/domains/job_creation/services/jd_enrichment.py (F1 sync). "
        "-> Fix: renomeie a outra (job_management async) para "
        "JobManagementJdEnrichmentService e atualize os imports."
    )
