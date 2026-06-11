"""
JobCreationAPIClient — Rails API client for job creation wizard.

Handles: create job, update job, publish, unpublish, get screening config,
get calibration candidates, submit calibration feedback.

Follows same pattern as JobsAPIClient (httpx, OTT auth, context tracking).
"""

import logging
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

import httpx
import uuid

from app.core.config import settings  # LIA-D01: Fix import path (was app.config.settings)
from app.services.ott_service import get_ott_service

logger = logging.getLogger(__name__)

# Sprint L+M canonical version marker — bump on each api_client revision.
# Searchable in logs: "[JobCreationAPI VERSION=" — proves which build is loaded.
API_CLIENT_VERSION = "sprint-L-bulletproof-2026-05-21"
logger.info("[JobCreationAPI VERSION=%s] module loaded", API_CLIENT_VERSION)


@dataclass
class APIResponse:
    success: bool
    data: Any = None
    meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


def _coerce_str_list(items):
    """Coerce list elements to strings — Pydantic models, dicts, or scalars."""
    out = []
    for x in items or []:
        if x is None:
            continue
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            # Try common key names from EnrichedJD shape
            v = x.get("skill") or x.get("competencia") or x.get("technology") or x.get("name") or x.get("text") or x.get("description")
            if v:
                out.append(str(v))
            else:
                out.append(str(x))
        elif hasattr(x, "model_dump"):
            d = x.model_dump()
            v = d.get("skill") or d.get("competencia") or d.get("name") or d.get("text")
            if v:
                out.append(str(v))
        else:
            out.append(str(x))
    return out


def _coerce_jsonable(items):
    """Coerce Pydantic models or other non-jsonable to plain dicts/scalars."""
    out = []
    for x in items or []:
        if hasattr(x, "model_dump"):
            out.append(x.model_dump())
        elif isinstance(x, (dict, str, int, float, bool, type(None))):
            out.append(x)
        else:
            out.append(str(x))
    return out


class JobCreationAPIClient:

    def __init__(self, context=None):
        self.settings = settings  # LIA-D01: settings is a singleton, not a function
        # Sprint F.5 fix (2026-05-20): Settings doesn't expose `ats_api` /
        # `rails_api` nested config — defensive lookup with env-var fallback
        # mirroring the canonical pattern (rails_jwt.py, _handler_hooks.py,
        # rails_health.py: all use `os.environ.get("RAILS_API_URL", "")`).
        # Without this, publish_node crashed with AttributeError on first
        # touch, blocking the wizard E2E from ever reaching job-vacancy
        # creation in production-shaped flows.
        import os as _os
        _ats_url = getattr(getattr(self.settings, "ats_api", None), "base_url", None)             or getattr(getattr(self.settings, "rails_api", None), "base_url", None)             or _os.environ.get("RAILS_API_URL", "")             or _os.environ.get("RAILS_BACKEND_URL", "")
        _ats_timeout = getattr(getattr(self.settings, "rails_api", None), "timeout", None)             or getattr(getattr(self.settings, "ats_api", None), "timeout", None)             or float(_os.environ.get("RAILS_API_TIMEOUT", "30"))
        self.base_url = _ats_url.rstrip("/") if _ats_url else ""
        self.timeout = _ats_timeout
        self._ott_service = get_ott_service()
        self._context = context

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._context and self._context.auth_token:
            headers["Authorization"] = f"Bearer {self._context.auth_token}"
        else:
            headers.update(self._ott_service.get_auth_header())
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> APIResponse:
        url = f"{self.base_url}{path}"
        start = time.time()

        # W2-009 (2026-05-22): Idempotency-Key em mutations Rails.
        request_headers = dict(self._get_headers())
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            request_headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method, url,
                    headers=request_headers,
                    params=params,
                    json=json_body,
                )

                if response.status_code == 401:
                    self._ott_service.invalidate()
                    # 401 retry: rebuild headers (OTT token refreshed) but keep same Idempotency-Key
                    request_headers = dict(self._get_headers())
                    if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
                        request_headers["Idempotency-Key"] = idempotency_key or request_headers.get("Idempotency-Key") or str(uuid.uuid4())
                    response = client.request(
                        method, url,
                        headers=request_headers,
                        params=params,
                        json=json_body,
                    )

                duration = (time.time() - start) * 1000

                if response.status_code >= 400:
                    error_body = response.text[:500] if response.text else "No body"
                    logger.error("[JobCreationAPI] HTTP %d %s %s: %s", response.status_code, method, path, error_body)
                    return APIResponse(success=False, error=f"HTTP {response.status_code}: {error_body[:200]}")

                data = response.json()
                logger.info("[JobCreationAPI] %s %s completed in %.0fms", method, path, duration)

                if self._context:
                    self._context.track_api_call(
                        endpoint=path, method=method, path=path,
                        params=params or json_body or {},
                        duration_ms=duration, status_code=response.status_code,
                    )

                return APIResponse(success=True, data=data)

        except httpx.TimeoutException:
            logger.error("[JobCreationAPI] Timeout %s %s", method, path)
            return APIResponse(success=False, error="Request timeout")
        except Exception as e:
            logger.error("[JobCreationAPI] Error %s %s: %s", method, path, e)
            return APIResponse(success=False, error=str(e))

    # -------------------------------------------------------------------
    # Job CRUD
    # -------------------------------------------------------------------

    def create_job(self, job_data: Dict[str, Any]) -> APIResponse:
        """Create a new job via Rails API.

        Args:
            job_data: Dict with title, description, department, seniority,
                     location, salary_range, benefits, etc.

        Sprint F.5 dev fallback (2026-05-20): when ``self.base_url`` is empty
        (Rails not configured in this env) AND
        ``LIA_DEV_LOCAL_PUBLISH=1``, INSERT directly into local
        ``job_vacancies`` table so the wizard E2E can validate
        ``job_vacancy_id != None`` without booting Rails. Production with
        ``RAILS_API_URL`` set hits the original path.
        """
        import os as _os
        logger.info(
            "[JobCreationAPI create_job ENTRY] VERSION=%s base_url=%r keys=%s",
            API_CLIENT_VERSION, self.base_url, sorted(list((job_data or {}).keys())),
        )
        if not self.base_url:  # Sprint F.5: Rails not configured — dev-local INSERT path
            try:
                return self._create_job_local(job_data)
            except Exception as e:
                logger.error("[JobCreationAPI] dev-local create_job failed: %s", e, exc_info=True)
                return APIResponse(success=False, error=f"dev-local insert failed: {e}")
        # Rails (fora de foco do publish dev-local): envia apenas os NOMES dos
        # beneficios p/ nao quebrar com o shape rico VagaBenefit. O shape
        # completo so e persistido no caminho dev-local (Postgres via FastAPI).
        from app.domains.job_creation.helpers.vaga_benefits import to_rails_names
        rails_job = dict(job_data)
        rails_job["benefits"] = to_rails_names(job_data.get("benefits"))
        return self._request("POST", "/api/v1/jobs", json_body={"job": rails_job})

    def _create_job_local(self, job_data: Dict[str, Any]) -> APIResponse:
        """Dev-only fallback: INSERT into local job_vacancies via psycopg2.

        Schema mirrored from libs/models/lia_models/job_vacancy.py:JobVacancy.
        Async sessionmaker (AsyncSessionLocal) can't be used from this sync
        context (publish_node runs in a thread executor). psycopg2 is bundled.
        Returns APIResponse with JSON:API shape that publish_node expects.

        Sprint L bulletproof rewrite (2026-05-20): five-layer dict-leak
        defense + per-param diagnostic logging fired BEFORE cursor.execute.
        Prior agents (Sprint J/K) added partial coerces but the diagnostic
        loop never fired in logs, meaning the dict leak slipped a defense.
        This rewrite consolidates into single canonical coerce + logs every
        param's type+repr before INSERT so future leaks are pinpointed by
        column name.
        """
        import os as _os
        import json as _json
        from app.domains.job_creation.helpers.vaga_benefits import (
            parse_vaga_benefits as _parse_vb,
            vaga_benefits_to_jsonb as _vb_jsonb,
        )
        from app.domains.job_creation.helpers.vaga_variable_comp import (
            parse_vaga_variable_comp as _parse_vc,
            vaga_variable_comp_to_jsonb as _vc_jsonb,
        )
        import uuid as _uuid
        import psycopg2

        company_id = (
            getattr(self._context, "company_id", None) if self._context else None
        ) or job_data.get("company_id") or "00000000-0000-4000-a000-000000000001"

        # --- LAYER 0: log INPUT shape before any processing -------------
        # If publish_node ever passes leaked dicts in unexpected fields,
        # we see EXACTLY which field upstream needs fixing.
        try:
            _input_summary = {
                k: type(v).__name__ for k, v in (job_data or {}).items()
            }
            logger.info(
                "[JobCreationAPI dev-local INPUT] keys/types: %s",
                _input_summary,
            )
        except Exception:
            logger.warning("[JobCreationAPI dev-local INPUT] could not summarize")

        # --- LAYER 1: bulletproof scalar coerce -------------------------
        def _bp_str(v, max_chars=2000):
            """Last-resort: ANY input -> safe str|None for VARCHAR/TEXT."""
            if v is None or v == "":
                return None
            if isinstance(v, str):
                return v[:max_chars]
            if isinstance(v, bool):
                return str(v)
            if isinstance(v, (int, float)):
                return str(v)
            if isinstance(v, dict):
                # Try common key names from EnrichedJD shape
                for k in ("text", "value", "title", "name", "label", "skill",
                          "description", "padronizado", "preferred"):
                    if v.get(k) and isinstance(v.get(k), (str, int, float)):
                        return str(v[k])[:max_chars]
                try:
                    return _json.dumps(v, default=str, ensure_ascii=False)[:max_chars]
                except Exception:
                    return str(v)[:max_chars]
            if isinstance(v, (list, tuple, set)):
                try:
                    return _json.dumps(list(v), default=str, ensure_ascii=False)[:max_chars]
                except Exception:
                    return ", ".join(str(x) for x in list(v)[:5])[:max_chars]
            # Catch psycopg2 Json wrappers, Pydantic models, anything else
            if hasattr(v, "model_dump"):
                try:
                    return _json.dumps(v.model_dump(), default=str, ensure_ascii=False)[:max_chars]
                except Exception:
                    return str(v)[:max_chars]
            return str(v)[:max_chars]

        # --- LAYER 2: bulletproof jsonable coerce (for JSONB columns) ---
        def _bp_jsonable(v):
            """For JSONB columns - ensure psycopg2-jsonb-adaptable structure.

            Fix (2026-05-21 DB-poisoning bug): for a string input, ONLY treat it
            as JSON if it actually looks like JSON (starts with [, {, ", digit,
            true/false/null). Otherwise return the bare string. Old behavior
            of wrapping in `[v]` on json.loads failure poisoned tech_req /
            beh_comp JSON columns with `[["Python"]]` instead of `["Python"]`.
            """
            if v is None:
                return None
            if isinstance(v, str):
                s = v.strip()
                if s and s[0] in '[{"-0123456789' or s in ("true", "false", "null"):
                    try:
                        return _json.loads(v)
                    except Exception:
                        return v  # return raw str, NOT [v]
                return v  # plain bare string -> return as-is
            if hasattr(v, "model_dump"):
                v = v.model_dump()
            if isinstance(v, dict):
                return {k: _bp_jsonable(val) for k, val in v.items()}
            if isinstance(v, (list, tuple, set)):
                return [_bp_jsonable(x) for x in v]
            if isinstance(v, (str, int, float, bool)):
                return v
            return str(v)

        # --- LAYER 3: bulletproof list-of-str coerce --------------------
        def _bp_str_list(items):
            """For requirements/responsibilities (text[]): flat list of strings.

            Handles deep cases observed in prod (2026-05-21):
            - None / "" -> []
            - "Python" -> ["Python"]
            - ["Python", "AWS"] -> ["Python", "AWS"]
            - [["Python"], ["AWS"]] -> ["Python", "AWS"]  (flatten one level)
            - [{"skill": "Python"}, {"text": "AWS"}] -> ["Python", "AWS"]
            - mixed -> coerced via _bp_str per item, flat
            """
            # Normalize input to a flat iterable
            if items is None:
                return []
            if isinstance(items, str):
                return [items[:500]] if items else []
            if isinstance(items, dict):
                s = _bp_str(items, max_chars=500)
                return [s] if s else []
            if not isinstance(items, (list, tuple, set)):
                s = _bp_str(items, max_chars=500)
                return [s] if s else []
            out = []
            for x in items:
                if x is None:
                    continue
                # Flatten one level: nested list -> recurse
                if isinstance(x, (list, tuple, set)):
                    out.extend(_bp_str_list(x))
                    continue
                s = _bp_str(x, max_chars=500)
                if s:
                    out.append(s)
            return out

        new_id = _uuid.uuid4()

        # Extract & coerce scalars
        title = _bp_str(job_data.get("title")) or "(sem titulo)"
        description = _bp_str(job_data.get("description"), max_chars=10000) or ""
        department = _bp_str(job_data.get("department"))
        location = _bp_str(job_data.get("location"))
        work_model = _bp_str(job_data.get("work_model"))
        seniority = _bp_str(job_data.get("seniority"))

        # FASE 5 / P0-A / P0-B: campos que o publish_node monta mas que o
        # INSERT dev-local antes descartava silenciosamente (gap half-shipped).
        employment_type = _bp_str(job_data.get("employment_type"))
        manager = _bp_str(job_data.get("manager"), max_chars=255)
        manager_email = _bp_str(job_data.get("manager_email"), max_chars=255)
        salary_range_jsonb = (
            _json.dumps(_bp_jsonable(job_data.get("salary_range")),
                        default=str, ensure_ascii=False)
            if job_data.get("salary_range") else None
        )

        # Skills list extraction (text[] column "requirements")
        tech_reqs_raw = job_data.get("technical_requirements") or []
        skills_list = []
        for tr in tech_reqs_raw:
            if isinstance(tr, dict):
                s = tr.get("skill") or tr.get("technology") or tr.get("name") or tr.get("text")
                if s:
                    skills_list.append(_bp_str(s, max_chars=300) or "")
            elif tr is not None:
                skills_list.append(_bp_str(tr, max_chars=300) or "")
        skills_list = [s for s in skills_list if s]

        # Responsibilities (text[] column)
        resp_list = _bp_str_list(job_data.get("responsibilities") or [])

        # JSONB payloads
        tech_reqs_jsonb = _json.dumps(_bp_jsonable(tech_reqs_raw), default=str, ensure_ascii=False)
        beh_comp_jsonb = _json.dumps(
            _bp_jsonable(job_data.get("behavioral_competencies") or []),
            default=str, ensure_ascii=False,
        )
        languages_jsonb = _json.dumps(
            _bp_jsonable(job_data.get("languages") or []),
            default=str, ensure_ascii=False,
        )
        # P0 fix 2026-05-31: beneficios eram montados no state mas NUNCA
        # entravam no INSERT dev-local (coluna existia, nada populava).
        # Normaliza para o shape canonical VagaBenefit (snapshot+ref).
        benefits_jsonb = _json.dumps(
            _bp_jsonable(_vb_jsonb(_parse_vb(job_data.get("benefits") or []))),
            default=str, ensure_ascii=False,
        )
        variable_comp_jsonb = _json.dumps(
            _bp_jsonable(_vc_jsonb(_parse_vc(job_data.get("variable_compensation") or []))),
            default=str, ensure_ascii=False,
        )

        # --- LAYER 4: canonical column->param mapping (no positional drift) ---
        _columns = [
            "id", "company_id", "title", "description", "department",
            "location", "work_model", "seniority_level", "requirements",
            "responsibilities", "technical_requirements",
            "behavioral_competencies", "languages", "benefits", "variable_compensation", "status",
            "employment_type", "manager", "manager_email", "salary_range",
            "created_at", "updated_at",
        ]
        # Sprint O.2: explicit timestamps (belt-and-suspenders with DB server_default)
        _now_utc = datetime.now(timezone.utc)
        _params_raw = [
            str(new_id), str(company_id), title, description, department,
            location, work_model, seniority, skills_list, resp_list,
            tech_reqs_jsonb, beh_comp_jsonb, languages_jsonb, benefits_jsonb, variable_comp_jsonb, "Rascunho",
            employment_type, manager, manager_email, salary_range_jsonb,
            _now_utc, _now_utc,
        ]

        # --- LAYER 5: per-param sanity + ULTRA defensive last-mile coerce ---
        _params = []
        _safe_scalar_types = (str, int, float, bool, type(None), datetime)
        for _col, _val in zip(_columns, _params_raw):
            if _col in ("requirements", "responsibilities"):
                # text[] columns - must be list of str
                if not isinstance(_val, list):
                    logger.warning(
                        "[JobCreationAPI dev-local INSERT] col=%s NOT list (type=%s) - coercing",
                        _col, type(_val).__name__,
                    )
                    _val = [_bp_str(_val) or ""]
                _safe = []
                for _x in _val:
                    if isinstance(_x, str):
                        _safe.append(_x)
                    else:
                        logger.warning(
                            "[JobCreationAPI dev-local INSERT] col=%s element non-str (type=%s) - coercing",
                            _col, type(_x).__name__,
                        )
                        _safe.append(_bp_str(_x) or "")
                _params.append(_safe)
            elif _col in ("technical_requirements", "behavioral_competencies", "languages", "benefits", "variable_compensation", "salary_range"):
                # JSONB columns - must be str (json-encoded) ou None (SQL NULL p/ salary_range)
                if _val is not None and not isinstance(_val, str):
                    logger.warning(
                        "[JobCreationAPI dev-local INSERT] col=%s JSONB NOT str (type=%s) - re-encoding",
                        _col, type(_val).__name__,
                    )
                    _val = _json.dumps(_bp_jsonable(_val), default=str, ensure_ascii=False)
                _params.append(_val)
            else:
                # Scalar columns - must be str|None
                if not isinstance(_val, _safe_scalar_types):
                    logger.error(
                        "[JobCreationAPI dev-local INSERT] col=%s LEAK type=%s repr=%r - bulletproof coercing",
                        _col, type(_val).__name__, str(_val)[:120],
                    )
                    _val = _bp_str(_val)
                _params.append(_val)

        # --- LAYER 6: BEFORE-execute diagnostic log (fires UNCONDITIONALLY) ---
        # Even if cur.execute raises immediately, we have the param shape on disk.
        try:
            _diag = [
                (i, _columns[i], type(p).__name__, (str(p)[:60] + ("..." if p and len(str(p)) > 60 else "")) if p is not None else "None")
                for i, p in enumerate(_params)
            ]
            logger.info(
                "[JobCreationAPI dev-local INSERT] %d params:\n%s",
                len(_params),
                "\n".join(f"  [{i}] {col:30s} type={t:10s} val={v}" for i, col, t, v in _diag),
            )
        except Exception as _e:
            logger.warning("[JobCreationAPI dev-local INSERT] diag log failed: %s", _e)

        # --- DB INSERT (sync psycopg2, runs in thread executor) ---------
        db_url = _os.environ["DATABASE_URL"]
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = psycopg2.connect(sync_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO job_vacancies
                    (id, company_id, title, description, department, location,
                     work_model, seniority_level, requirements, responsibilities,
                     technical_requirements, behavioral_competencies, languages, benefits, variable_compensation, status,
                     employment_type, manager, manager_email, salary_range,
                     created_at, updated_at)
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s,
                     %s, %s, %s, %s::jsonb,
                     %s, %s)
                    RETURNING id
                    """,
                    _params,
                )
                row = cur.fetchone()
                conn.commit()
                new_id_str = str(row[0])
        finally:
            conn.close()

        logger.info(
            "[JobCreationAPI] dev-local INSERT OK id=%s title=%r",
            new_id_str, title,
        )
        return APIResponse(
            success=True,
            data={
                "data": {
                    "id": new_id_str,
                    "attributes": {
                        "id": new_id_str,
                        "uid": new_id_str,
                        "title": title,
                        "status": "Rascunho",
                    },
                },
            },
        )

    def update_job(self, job_id: int, updates: Dict[str, Any]) -> APIResponse:
        """Update an existing job."""
        return self._request("PATCH", f"/api/v1/jobs/{job_id}", json_body={"job": updates})

    def get_job(self, job_id: int) -> APIResponse:
        """Get job details."""
        return self._request("GET", f"/api/v1/jobs/{job_id}")

    # -------------------------------------------------------------------
    # Publishing
    # -------------------------------------------------------------------

    def publish_job(self, job_id: int, platforms: List[str], sourcing_mode: str = "local") -> APIResponse:
        """Publish job to specified platforms.

        Dev-local (base_url vazio — Rails fora, FastAPI canonical): ativa a
        vaga (status Rascunho→Ativa) via JobVacancyLifecycleRepository e marca
        os flags de plataforma. Mesma lógica do endpoint FastAPI
        ``/jobs/{id}/publish`` (DRY).
        """
        if not self.base_url:
            return self._publish_job_local(job_id, platforms or [])
        return self._request("POST", f"/api/v1/jobs/{job_id}/publish", json_body={
            "platforms": platforms,
            "sourcing_mode": sourcing_mode,
        })

    def _devlocal_conn(self):
        """psycopg2 sync connection (dev-local). Mesma DSN do _create_job_local.

        Sync por design: o engine async global (AsyncSessionLocal) tem pool
        preso ao loop que o criou; múltiplos asyncio.run() em sequência (publish
        + share_link no mesmo turno) batem em 'Future attached to a different
        loop'. psycopg2 sync evita isso — padrão canonical dev-local deste arquivo.
        """
        import os as _os
        import psycopg2
        db_url = _os.environ["DATABASE_URL"]
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        return psycopg2.connect(sync_url)

    def _publish_job_local(self, job_id, platforms: List[str]) -> APIResponse:
        """Dev-local publish: status→Ativa + open_date + flags de plataforma."""
        _p = {str(x).lower() for x in (platforms or [])}
        try:
            conn = self._devlocal_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE job_vacancies SET
                            status = 'Ativa',
                            open_date = COALESCE(open_date, NOW()),
                            published_linkedin = %s,
                            published_website = %s,
                            published_indeed = %s,
                            last_published_at = NOW(),
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                        """,
                        (
                            "linkedin" in _p,
                            "website" in _p,
                            "indeed" in _p,
                            str(job_id),
                        ),
                    )
                    row = cur.fetchone()
                    conn.commit()
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001 — fail-loud
            logger.error("[JobCreationAPI] dev-local publish failed: %s", e, exc_info=True)
            return APIResponse(success=False, error=f"dev-local publish failed: {e}")
        if not row:
            return APIResponse(success=False, error=f"vaga {job_id} não encontrada")
        logger.info("[JobCreationAPI] dev-local publish OK job=%s status=Ativa", job_id)
        return APIResponse(success=True, data={"status": "Ativa", "id": str(row[0])})

    def unpublish_job(self, job_id: int) -> APIResponse:
        """Unpublish a job."""
        return self._request("POST", f"/api/v1/jobs/{job_id}/unpublish")

    # -------------------------------------------------------------------
    # Screening configuration
    # -------------------------------------------------------------------

    def save_screening_config(
        self,
        job_id: int,
        questions: List[Dict[str, Any]],
        mode: str = "compact",
        eligibility_questions: Optional[List[Dict[str, Any]]] = None,
    ) -> APIResponse:
        """Save WSI screening questions for a job."""
        if not self.base_url:
            return self._save_screening_config_local(
                job_id, questions or [], mode, eligibility_questions or []
            )
        return self._request("POST", f"/api/v1/jobs/{job_id}/screening_config", json_body={
            "screening_questions": questions,
            "screening_mode": mode,
            "eligibility_questions": eligibility_questions or [],
        })

    def _save_screening_config_local(
        self, job_id, questions: List[Dict[str, Any]], mode: str,
        eligibility: List[Dict[str, Any]],
    ) -> APIResponse:
        """Dev-local screening persist: merge no screening_config (jsonb)."""
        import json as _json
        new_cfg = {
            "screening_questions": questions,
            "screening_mode": mode,
            "eligibility_questions": eligibility,
        }
        try:
            conn = self._devlocal_conn()
            try:
                with conn.cursor() as cur:
                    # merge: preserva chaves existentes + sobrescreve as novas.
                    cur.execute(
                        """
                        UPDATE job_vacancies SET
                            screening_config = COALESCE(screening_config, '{}'::jsonb) || %s::jsonb,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                        """,
                        (_json.dumps(new_cfg, ensure_ascii=False), str(job_id)),
                    )
                    row = cur.fetchone()
                    conn.commit()
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001 — fail-loud
            logger.error("[JobCreationAPI] dev-local screening_config failed: %s", e, exc_info=True)
            return APIResponse(success=False, error=f"dev-local screening_config failed: {e}")
        if not row:
            return APIResponse(success=False, error=f"vaga {job_id} não encontrada")
        return APIResponse(success=True, data={"saved": len(questions)})


    def save_question_set(
        self,
        job_id: str,
        questions: List[Dict[str, Any]],
        mode: str = "compact",
        seniority_level: Optional[str] = None,
    ) -> "APIResponse":
        """Cria question set versionado no lia-agent-system.

        Chamado pelo publish do wizard para garantir que a triagem use as
        perguntas aprovadas pelo recrutador (HITL #2) em vez de regenerar
        do zero via WSIQuestionGenerator.

        Endpoint destino: POST /api/v1/wsi/questions/save
        (lia-agent-system, nao Rails -- usa LIA_API_URL se disponivel).
        """
        payload: Dict[str, Any] = {
            "job_id": str(job_id),
            "questions": questions,
            "source": "wizard_approved",
        }
        if seniority_level:
            payload["seniority_level"] = seniority_level
        if mode:
            payload["mode"] = mode

        # Tentar lia-agent-system diretamente; fallback: sem question_set
        # (triagem usara regeneracao -- nao e bloqueador de publicacao).
        lia_url = (
            getattr(getattr(self.settings, "lia_api", None), "base_url", None)
            or _os.environ.get("LIA_API_URL", "")
            or _os.environ.get("FASTAPI_URL", "")
        )
        if not lia_url:
            # Dev-local: gravar via devlocal helper (psycopg2 direto)
            return self._save_question_set_local(job_id, questions, mode, seniority_level)

        url = f"{lia_url.rstrip('/')}/api/v1/wsi/questions/save"
        try:
            import httpx as _httpx
            headers = self._get_headers()
            with _httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return APIResponse(success=True, data=resp.json())
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[JobCreationAPI] save_question_set failed: %s", exc, exc_info=True,
                extra={"job_id": job_id},
            )
            return APIResponse(success=False, error=str(exc))

    def _save_question_set_local(
        self,
        job_id: str,
        questions: List[Dict[str, Any]],
        mode: str,
        seniority_level: Optional[str],
    ) -> "APIResponse":
        """Dev-local: insere diretamente na tabela screening_question_sets."""
        import json as _json
        import uuid as _uuid
        try:
            conn = self._devlocal_conn()
            try:
                with conn.cursor() as cur:
                    set_id = str(_uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO screening_question_sets
                            (id, job_vacancy_id, questions, source, created_at, updated_at)
                        VALUES (%s, %s, %s::jsonb, %s, NOW(), NOW())
                        ON CONFLICT (job_vacancy_id) DO UPDATE SET
                            questions = EXCLUDED.questions,
                            source = EXCLUDED.source,
                            updated_at = NOW()
                        """,
                        (
                            set_id,
                            str(job_id),
                            _json.dumps(questions, ensure_ascii=False),
                            "wizard_approved",
                        ),
                    )
                    conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[JobCreationAPI] _save_question_set_local: tabela ausente ou erro: %s", exc
            )
            return APIResponse(success=False, error=f"dev-local question_set failed: {exc}")
        return APIResponse(success=True, data={"saved": len(questions)})

    # -------------------------------------------------------------------
    # Calibration
    # -------------------------------------------------------------------

    def get_calibration_candidates(self, job_id: int, limit: int = 5) -> APIResponse:
        """Get candidate profiles for calibration."""
        return self._request("GET", f"/api/v1/jobs/{job_id}/calibration_candidates", params={
            "limit": limit,
        })

    def submit_calibration_feedback(
        self,
        job_id: int,
        candidate_id: str,
        decision: str,
        reason: Optional[str] = None,
    ) -> APIResponse:
        """Submit calibration decision for a candidate."""
        return self._request("POST", f"/api/v1/jobs/{job_id}/calibration_feedback", json_body={
            "candidate_id": candidate_id,
            "decision": decision,
            "reason": reason,
        })

    # -------------------------------------------------------------------
    # Company configuration
    # -------------------------------------------------------------------

    def get_company_defaults(self, workspace_id: int | str) -> APIResponse:
        """Get company configuration defaults (recruitment policies, eligibility, etc.)."""
        return self._request("GET", f"/api/v1/workspaces/{workspace_id}/recruitment_config")

    # -------------------------------------------------------------------
    # JD Enrichment (delegates to Python backend WSI service)
    # -------------------------------------------------------------------

    def evaluate_jd(self, jd_text: str, title: str = "", seniority: str = "") -> APIResponse:
        """Call WSI JD evaluation endpoint."""
        return self._request("POST", "/api/v1/wsi/jd-evaluate", json_body={
            "job_description": jd_text,
            "title": title,
            "seniority": seniority,
        })

    # -------------------------------------------------------------------
    # Share link
    # -------------------------------------------------------------------

    def get_share_link(self, job_id: int) -> APIResponse:
        """Get the public share link for a published job.

        Dev-local: gera o public_slug (se ausente) via repo canonical e
        devolve a URL pública. Mesma forma do endpoint FastAPI
        ``/job-vacancies/{id}/share-link`` (DRY).
        """
        if not self.base_url:
            return self._get_share_link_local(job_id)
        return self._request("GET", f"/api/v1/jobs/{job_id}/share_link")

    def _get_share_link_local(self, job_id) -> APIResponse:
        """Dev-local share link: gera public_slug (se ausente) + URL pública."""
        import secrets as _secrets
        from app.api.v1.job_vacancies._shared import generate_slug
        try:
            conn = self._devlocal_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT public_slug, title FROM job_vacancies WHERE id = %s",
                        (str(job_id),),
                    )
                    row = cur.fetchone()
                    if not row:
                        return APIResponse(success=False, error=f"vaga {job_id} não encontrada")
                    slug, title = row[0], row[1]
                    if not slug:
                        # token curto garante unicidade sem round-trip de checagem.
                        slug = generate_slug(title or "vaga", _secrets.token_hex(2))
                        cur.execute(
                            "UPDATE job_vacancies SET public_slug = %s, updated_at = NOW() WHERE id = %s",
                            (slug, str(job_id)),
                        )
                        conn.commit()
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001 — fail-loud
            logger.error("[JobCreationAPI] dev-local share_link failed: %s", e, exc_info=True)
            return APIResponse(success=False, error=f"dev-local share_link failed: {e}")
        return APIResponse(
            success=True,
            data={
                "share_link": f"https://app.wedotalent.com/jobs/{slug}",
                "public_url": f"/vagas/{slug}",
                "slug": slug,
            },
        )
