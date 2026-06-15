"""
FairnessPolicyService — 3-layer composable fairness policy engine.

Loads and composes effective policies from:
  Layer 1: Platform-general rules (scope='platform_general', domain=None)
  Layer 2: Platform-domain rules (scope='platform_domain', domain=<domain>)
  Layer 3: Tenant-domain rules (scope='tenant', domain=<domain>, company_id=<id>)

Each layer can only amplify/harden rules from the layer below (never soften locked rules).

Compliance: LGPD Art.6/11 + EU AI Act Annex III item 4
ADR ref: ADR-001 (storage) + sec9 Definicoes Arquiteturais v0.4.1
"""
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_key(tenant_id: str | None, domain: str) -> str:
    tid = tenant_id or "platform"
    return f"fairness:effective:{tid}:{domain}"


class FairnessPolicyService:
    """
    Composable 3-layer fairness policy service.

    Usage:
        service = FairnessPolicyService()
        policy = await service.load_effective_policy(tenant_id, domain, db)
        clean_input = service.apply_input_filter(raw_input, policy)
        allowed, reason = await service.allows_automated(decision_type, confidence, policy, ...)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def load_effective_policy(
        self,
        tenant_id: str | None,
        domain: str,
        db: "AsyncSession",
    ) -> dict:
        """
        Composes Effective Policy for (tenant_id, domain) across 3 layers.

        Returns dict: {rule_type: [merged_rules, ...]}
        Cache in Redis for 5 min (key: fairness:effective:{tenant_id}:{domain}).
        """
        cache_key = _cache_key(tenant_id, domain)

        # Try Redis cache first (fail-open)
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        from sqlalchemy import select, or_
        from lia_models.fairness_policies import FairnessPolicyRule

        # Layer 1: platform_general (domain=None, company_id=None)
        stmt1 = select(FairnessPolicyRule).where(
            FairnessPolicyRule.scope == "platform_general",
            FairnessPolicyRule.company_id.is_(None),
            FairnessPolicyRule.status.in_(["published", "active"]),
        )

        # Layer 2: platform_domain (domain=domain, company_id=None)
        stmt2 = select(FairnessPolicyRule).where(
            FairnessPolicyRule.scope == "platform_domain",
            FairnessPolicyRule.domain == domain,
            FairnessPolicyRule.company_id.is_(None),
            FairnessPolicyRule.status.in_(["published", "active"]),
        )

        # Layer 3: tenant (company_id=tenant_id, domain=domain)
        stmt3 = select(FairnessPolicyRule).where(
            FairnessPolicyRule.scope == "tenant",
            FairnessPolicyRule.company_id == tenant_id,
            FairnessPolicyRule.domain == domain,
            FairnessPolicyRule.status.in_(["published", "active"]),
        ) if tenant_id else None

        result: dict[str, list] = {}

        for stmt in [stmt1, stmt2] + ([stmt3] if stmt3 is not None else []):
            rows = (await db.execute(stmt)).scalars().all()
            for rule in rows:
                rule_type = rule.rule_type
                if rule_type not in result:
                    result[rule_type] = []
                result[rule_type].append({
                    "id": str(rule.id),
                    "scope": rule.scope,
                    "domain": rule.domain,
                    "is_locked": rule.is_locked,
                    "body_json": rule.body_json,
                })

        # Merge lists/thresholds across layers (layers can only harden)
        merged = self._merge_layers(result)

        # Cache result (fail-open)
        await self._cache_set(cache_key, merged, ttl=_CACHE_TTL_SECONDS)

        return merged

    def apply_input_filter(self, input_dict: dict, effective_policy: dict) -> dict:
        """
        Removes/masks fields from input_dict based on effective_policy.

        Applies:
        - 'mandatory_anonymization' rules: remove fields listed in body_json['fields']
        - 'blocked_attribute' rules: remove attributes listed in body_json['attributes']

        Returns clean dict (original not mutated).
        """
        result = dict(input_dict)

        for rule in effective_policy.get("mandatory_anonymization", []):
            fields = rule.get("body_json", {}).get("fields", [])
            for f in fields:
                result.pop(f, None)

        for rule in effective_policy.get("blocked_attribute", []):
            attrs = rule.get("body_json", {}).get("attributes", [])
            for a in attrs:
                result.pop(a, None)

        return result

    def validate_query_filters(self, filters: dict, effective_policy: dict) -> list[str]:
        """
        Verifica se filters contêm termos de 'linguistic_banlist' rules.

        Suporta dois formatos de body_json:
        - {"terms": [...]} -- lista direta
        - {"terms_pt": [...], "terms_en": [...]} -- separados por idioma (Regra 7 do seed)
        - {"categories": {...}} -- categorias de regex (Regras 5/6) -- delega ao FairnessGuard

        Returns list of violations (vazia = OK).
        """
        violations: list[str] = []
        text_to_check = " ".join(str(v) for v in filters.values()).lower()

        for rule in effective_policy.get("linguistic_banlist", []):
            body = rule.get("body_json", {})

            # Formato 1: lista direta {"terms": [...]}
            direct_terms = body.get("terms", [])

            # Formato 2: separados por idioma {"terms_pt": [...], "terms_en": [...]}
            pt_terms = body.get("terms_pt", [])
            en_terms = body.get("terms_en", [])

            all_terms = direct_terms + pt_terms + en_terms

            for term in all_terms:
                if term.lower() in text_to_check:
                    violations.append(f"Termo discriminatorio detectado: '{term}'")

            # Formato 3: categorias de regex (Regras 5/6) -- delega ao FairnessGuard
            categories = body.get("categories")
            if categories and body.get("detection_mode") in ("regex_hard_block", "regex_warn"):
                try:
                    from app.shared.compliance.fairness_guard import FairnessGuard
                    guard = FairnessGuard(strict=False)
                    for query_val in filters.values():
                        if not isinstance(query_val, str):
                            continue
                        result = guard.check(query_val)
                        if result.is_blocked:
                            violations.append(
                                f"Categoria discriminatoria detectada: "
                                f"'{result.category}' -- termos: {result.blocked_terms[:3]}"
                            )
                except Exception as exc:
                    logger.debug("[validate_query_filters] FairnessGuard skip: %s", exc)

        return violations

    async def allows_automated(
        self,
        decision_type: str,
        confidence: float,
        effective_policy: dict,
        tenant_id: str,
        domain: str,
        db: "AsyncSession",
    ) -> tuple[bool, str]:
        """
        Checks whether an automated decision is allowed.

        1. If decision_type is in 'human_in_the_loop' rules → (False, reason)
        2. If confidence < min_confidence in 'decision_threshold' → (False, reason)

        Returns (allowed, reason). Logs violation to DB if not allowed.
        """
        # Check human_in_the_loop
        for rule in effective_policy.get("human_in_the_loop", []):
            body = rule.get("body_json", {})
            decision_types = body.get("decision_types", [])
            if decision_type in decision_types:
                reason = (
                    f"Decisão '{decision_type}' requer aprovação humana obrigatória "
                    f"(human_in_the_loop policy, bypass_allowed={body.get('bypass_allowed', False)})"
                )
                await self.audit_decision(
                    tenant_id=tenant_id,
                    domain=domain,
                    decision_type=decision_type,
                    confidence=confidence,
                    evidence={"decision_type": decision_type},
                    effective_policy=effective_policy,
                    was_blocked=True,
                    correlation_id=None,
                    db=db,
                    rule_id=rule.get("id"),
                    rule_type="human_in_the_loop",
                    violation_type="human_approval_required",
                )
                return False, reason

        # Check decision_threshold
        for rule in effective_policy.get("decision_threshold", []):
            body = rule.get("body_json", {})
            min_confidence = body.get("min_confidence", 0.75)
            applies_to = body.get("applies_to", [])
            if confidence < min_confidence:
                reason = (
                    f"Confiança {confidence:.2f} abaixo do mínimo {min_confidence:.2f} "
                    f"para decisão automática (applies_to={applies_to})"
                )
                await self.audit_decision(
                    tenant_id=tenant_id,
                    domain=domain,
                    decision_type=decision_type,
                    confidence=confidence,
                    evidence={"confidence": confidence, "min_confidence": min_confidence},
                    effective_policy=effective_policy,
                    was_blocked=True,
                    correlation_id=None,
                    db=db,
                    rule_id=rule.get("id"),
                    rule_type="decision_threshold",
                    violation_type="confidence_below_threshold",
                )
                return False, reason

        return True, ""

    async def audit_decision(
        self,
        tenant_id: str,
        domain: str,
        decision_type: str,
        confidence: float,
        evidence: dict,
        effective_policy: dict,
        was_blocked: bool,
        correlation_id: str | None,
        db: "AsyncSession",
        rule_id: str | None = None,
        rule_type: str = "unknown",
        violation_type: str = "policy_violation",
    ) -> str:
        """
        Writes a violation record to fairness_policy_violations.

        Returns the violation_id (UUID string).
        LGPD: input_snapshot_hash is SHA-256 of masked evidence (never raw PII).
        """
        from lia_models.fairness_policies import FairnessPolicyViolation
        import uuid as _uuid

        # Hash masked evidence for audit trail (no raw PII)
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        snapshot_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        violation_id = _uuid.uuid4()
        # Safely convert IDs — rule_id from test fixtures may be non-UUID strings
        try:
            _rule_id = _uuid.UUID(rule_id) if rule_id and isinstance(rule_id, str) else rule_id
        except (ValueError, AttributeError):
            _rule_id = None

        try:
            _company_uuid = _uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        except (ValueError, AttributeError):
            _company_uuid = None

        violation = FairnessPolicyViolation(
            id=violation_id,
            company_id=_company_uuid,
            domain=domain,
            rule_id=_rule_id,
            rule_type=rule_type,
            violation_type=violation_type,
            input_snapshot_hash=snapshot_hash,
            decision_context={
                "decision_type": decision_type,
                "confidence": confidence,
            },
            was_blocked=was_blocked,
            correlation_id=correlation_id,
        )
        db.add(violation)
        try:
            await db.flush()
        except Exception as exc:
            logger.error("[FairnessPolicyService] audit_decision flush error: %s", exc)

        return str(violation_id)

    def validate_tenant_override(
        self,
        tenant_rules: list[dict],
        platform_rules: list[dict],
    ) -> list[str]:
        """
        Validates that tenant rules do not soften locked platform rules.

        Returns list of errors (empty = OK).
        Checks:
        - decision_threshold: tenant.min_confidence >= platform.min_confidence
        - blocked_attribute: tenant cannot remove attributes
        - mandatory_anonymization: tenant cannot remove fields
        - human_in_the_loop: tenant cannot remove decision_types
        """
        errors: list[str] = []

        # Build platform index by rule_type (only locked rules matter)
        platform_by_type: dict[str, list[dict]] = {}
        for rule in platform_rules:
            if rule.get("is_locked", False):
                rt = rule.get("rule_type", "")
                platform_by_type.setdefault(rt, []).append(rule)

        for tenant_rule in tenant_rules:
            rt = tenant_rule.get("rule_type", "")
            body = tenant_rule.get("body_json", {})
            platform_locked = platform_by_type.get(rt, [])

            if not platform_locked:
                continue  # no locked platform rule for this type

            if rt == "decision_threshold":
                tenant_min = body.get("min_confidence", 0.0)
                for pr in platform_locked:
                    platform_min = pr.get("body_json", {}).get("min_confidence", 0.75)
                    if tenant_min < platform_min:
                        errors.append(
                            f"decision_threshold: tenant min_confidence {tenant_min} < "
                            f"platform min_confidence {platform_min} (locked)"
                        )

            elif rt == "blocked_attribute":
                tenant_attrs = set(body.get("attributes", []))
                for pr in platform_locked:
                    platform_attrs = set(pr.get("body_json", {}).get("attributes", []))
                    missing = platform_attrs - tenant_attrs
                    if missing:
                        errors.append(
                            f"blocked_attribute: tenant tentando remover atributos locked: {missing}"
                        )

            elif rt == "mandatory_anonymization":
                tenant_fields = set(body.get("fields", []))
                for pr in platform_locked:
                    platform_fields = set(pr.get("body_json", {}).get("fields", []))
                    missing = platform_fields - tenant_fields
                    if missing:
                        errors.append(
                            f"mandatory_anonymization: tenant tentando remover campos PII locked: {missing}"
                        )

            elif rt == "human_in_the_loop":
                tenant_dtypes = set(body.get("decision_types", []))
                for pr in platform_locked:
                    platform_dtypes = set(pr.get("body_json", {}).get("decision_types", []))
                    missing = platform_dtypes - tenant_dtypes
                    if missing:
                        errors.append(
                            f"human_in_the_loop: tenant tentando remover decision_types locked: {missing}"
                        )

        return errors

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _merge_layers(self, rules_by_type: dict[str, list]) -> dict[str, list]:
        """
        Merges rules of the same type across layers.
        Lists (attributes, fields, decision_types) are unioned.
        Thresholds (min_confidence) take the maximum (most strict).
        Returns same structure (rule_type -> list of merged rule dicts).
        """
        # For now: return as-is (composable merge is applied at consume time
        # in apply_input_filter and allows_automated by iterating all rules).
        # More sophisticated merging (dedup, override) can be added later.
        return rules_by_type

    async def _cache_get(self, key: str) -> dict | None:
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(_REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
            raw = await client.get(key)
            await client.aclose()
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.debug("[FairnessPolicyService] cache_get skip: %s", exc)
        return None

    async def _cache_set(self, key: str, value: dict, ttl: int = 300) -> None:
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(_REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
            await client.setex(key, ttl, json.dumps(value, default=str))
            await client.aclose()
        except Exception as exc:
            logger.debug("[FairnessPolicyService] cache_set skip: %s", exc)


# Module-level singleton for convenience imports
_fairness_service_instance: FairnessPolicyService | None = None


def _get_fairness_service() -> FairnessPolicyService:
    global _fairness_service_instance
    if _fairness_service_instance is None:
        _fairness_service_instance = FairnessPolicyService()
    return _fairness_service_instance
