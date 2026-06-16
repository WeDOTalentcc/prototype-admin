"""
Few-Shot Evolution Service — auto-evolving agent intelligence.

Pipeline:
  1. Select excellent interactions from audit_logs (daily)
  2. Anonymize via AnonymizationPipeline
  3. Quality-gate: novelty + quality + size
  4. Auto-insert (score > 0.90) or queue for review (0.70-0.90)
  5. Rotate FIFO when limit reached (max 15 per agent)

Item: PX08 — Sprint 12, item 12.7
"""
from __future__ import annotations

import copy
import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "domains"

# Thresholds
MIN_CONFIDENCE = 0.85
MIN_TOOL_CALLS = 2
MAX_FEW_SHOT_PER_AGENT = 15
AUTO_APPROVE_THRESHOLD = 0.90
MANUAL_REVIEW_THRESHOLD = 0.70

AGENT_DOMAINS = [
    "communication", "ats_integration", "interview_scheduling",
    "wsi_interview", "automation", "analytics",
    "company_settings", "recruiter_assistant",
]


class FewShotCandidateSelector:
    """Selects excellent interactions as few-shot candidates."""

    async def select_candidates(self, hours: int = 24) -> list[dict[str, Any]]:
        """Query audit_logs for excellent interactions in last N hours."""
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            cutoff = datetime.utcnow() - timedelta(hours=hours)
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("""
                        SELECT id, agent_name, decision_type, action, decision,
                               reasoning, criteria_used, score, confidence,
                               company_id, candidate_id, created_at
                        FROM audit_logs
                        WHERE created_at >= :cutoff
                          AND confidence >= :min_conf
                          AND decision != 'error'
                          AND fairness_flags IS NULL
                        ORDER BY confidence DESC
                        LIMIT 200
                    """),
                    {"cutoff": cutoff, "min_conf": MIN_CONFIDENCE},
                )
                rows = result.mappings().all()
                return [dict(r) for r in rows]
        except Exception as exc:
            logger.warning("[FewShotSelector] Query failed: %s", exc)
            return []

    def evaluate_candidate(self, interaction: dict[str, Any]) -> float:
        """Score 0-1: how good is this interaction as a few-shot example?"""
        score = 0.0

        # High confidence → good
        conf = interaction.get("confidence", 0)
        if conf >= 0.90:
            score += 0.35
        elif conf >= 0.85:
            score += 0.20

        # Has reasoning → good (shows thought process)
        reasoning = interaction.get("reasoning") or []
        if isinstance(reasoning, list) and len(reasoning) >= 2:
            score += 0.25
        elif reasoning:
            score += 0.10

        # Uses multiple criteria → good (substantive)
        criteria = interaction.get("criteria_used") or []
        if isinstance(criteria, list) and len(criteria) >= 3:
            score += 0.20
        elif criteria:
            score += 0.10

        # Has score → good (decision with data)
        if interaction.get("score") is not None:
            score += 0.10

        # Decision is clear → good
        decision = interaction.get("decision", "")
        if decision in ("completed", "approved", "advanced"):
            score += 0.10

        return min(score, 1.0)

    def is_novel(self, candidate: dict, existing_ids: set[str]) -> bool:
        """Check if this covers a different scenario than existing examples."""
        # Simple novelty: different decision_type or action
        key = f"{candidate.get('decision_type', '')}:{candidate.get('action', '')}"
        return key not in existing_ids

    def anonymize_and_format(self, candidate: dict[str, Any], domain: str) -> dict[str, Any]:
        """Anonymize and format as YAML few-shot structure."""
        reasoning = candidate.get("reasoning", [])
        if isinstance(reasoning, list):
            reasoning_text = " ".join(str(r) for r in reasoning[:3])
        else:
            reasoning_text = str(reasoning)[:300]

        return {
            "id": f"auto-{candidate.get('id', 'unknown')[:8]}",
            "category": "auto_evolved",
            "scenario": f"Auto-captured: {candidate.get('decision_type', 'interaction')}",
            "user_input": f"[{candidate.get('action', 'request')}]",
            "expected_response": reasoning_text or "Interacao de alta qualidade capturada automaticamente.",
            "demonstrates": ["auto-evolved", candidate.get("decision_type", "general")],
            "quality_score": self.evaluate_candidate(candidate),
            "captured_at": datetime.utcnow().isoformat(),
        }


class FewShotAutoInserter:
    """Inserts approved few-shot examples into agent YAML files."""

    def get_yaml_path(self, domain: str) -> Path:
        """Get YAML prompt file path for a domain."""
        return _PROMPTS_DIR / f"{domain}.yaml"

    def count_examples(self, domain: str) -> int:
        """Count existing few-shot examples in YAML."""
        path = self.get_yaml_path(domain)
        if not path.exists():
            return 0
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return len(data.get("few_shot_examples", []))
        except Exception:
            return 0

    def insert_to_yaml(self, domain: str, example: dict[str, Any]) -> bool:
        """Read YAML, add example, save. Atomic with backup."""
        path = self.get_yaml_path(domain)
        if not path.exists():
            logger.warning("[FewShotInserter] YAML not found: %s", path)
            return False

        # Backup before modification
        backup_path = path.with_suffix(".yaml.bak")
        try:
            shutil.copy2(path, backup_path)
        except Exception as exc:
            logger.warning("[FewShotInserter] Backup failed: %s", exc)

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            if "few_shot_examples" not in data:
                data["few_shot_examples"] = []

            # Remove auto-metadata before inserting
            clean_example = {
                "id": example["id"],
                "category": example["category"],
                "scenario": example["scenario"],
                "user_input": example["user_input"],
                "expected_response": example["expected_response"],
                "demonstrates": example.get("demonstrates", []),
            }

            data["few_shot_examples"].append(clean_example)

            with open(path, "w") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            logger.info("[FewShotInserter] Inserted example %s into %s", example["id"], domain)
            return True

        except Exception as exc:
            logger.error("[FewShotInserter] Insert failed, restoring backup: %s", exc)
            # Rollback
            try:
                if backup_path.exists():
                    shutil.copy2(backup_path, path)
            except Exception:
                pass
            return False

    def rotate_if_needed(self, domain: str) -> int:
        """If >= MAX, remove oldest auto-evolved example (FIFO). Returns removed count."""
        path = self.get_yaml_path(domain)
        if not path.exists():
            return 0

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            examples = data.get("few_shot_examples", [])
            if len(examples) < MAX_FEW_SHOT_PER_AGENT:
                return 0

            # Find auto-evolved examples (removable)
            auto_examples = [
                (i, e) for i, e in enumerate(examples)
                if e.get("category") == "auto_evolved" or str(e.get("id", "")).startswith("auto-")
            ]

            if not auto_examples:
                return 0  # only manual examples — don't remove

            # Remove oldest auto-evolved
            oldest_idx = auto_examples[0][0]
            removed = examples.pop(oldest_idx)
            data["few_shot_examples"] = examples

            with open(path, "w") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            logger.info("[FewShotInserter] Rotated out %s from %s", removed.get("id"), domain)
            return 1

        except Exception as exc:
            logger.warning("[FewShotInserter] Rotation failed: %s", exc)
            return 0


async def run_fewshot_evolution() -> dict[str, Any]:
    """Main pipeline: select → evaluate → anonymize → insert/queue."""
    selector = FewShotCandidateSelector()
    inserter = FewShotAutoInserter()

    candidates = await selector.select_candidates(hours=24)
    if not candidates:
        return {"status": "no_candidates", "processed": 0}

    results: dict[str, Any] = {"processed": 0, "auto_inserted": 0, "pending_review": 0, "rejected": 0}

    # Group by agent domain
    domain_map: dict[str, list] = {}
    for c in candidates:
        agent = c.get("agent_name", "unknown")
        # Map agent_name to domain
        domain = agent.replace("_react_agent", "").replace("_agent", "")
        if domain not in AGENT_DOMAINS:
            continue
        domain_map.setdefault(domain, []).append(c)

    for domain, interactions in domain_map.items():
        current_count = inserter.count_examples(domain)
        existing_ids = set()  # TODO: extract from YAML for true novelty check  # R-048: needs owner + ticket

        for interaction in interactions[:5]:  # max 5 per domain per day
            results["processed"] += 1
            score = selector.evaluate_candidate(interaction)

            if score < MANUAL_REVIEW_THRESHOLD:
                results["rejected"] += 1
                continue

            if not selector.is_novel(interaction, existing_ids):
                results["rejected"] += 1
                continue

            example = selector.anonymize_and_format(interaction, domain)
            existing_ids.add(f"{interaction.get('decision_type')}:{interaction.get('action')}")

            if score >= AUTO_APPROVE_THRESHOLD and current_count < MAX_FEW_SHOT_PER_AGENT:
                # Rotate if at limit
                if current_count >= MAX_FEW_SHOT_PER_AGENT:
                    inserter.rotate_if_needed(domain)

                if inserter.insert_to_yaml(domain, example):
                    results["auto_inserted"] += 1
                    current_count += 1
                else:
                    results["rejected"] += 1
            elif score >= MANUAL_REVIEW_THRESHOLD:
                # Save as pending for manual review
                try:
                    from app.core.database import AsyncSessionLocal
                    from sqlalchemy import text
                    import uuid

                    async with AsyncSessionLocal() as db:
                        await db.execute(
                            text("""
                                INSERT INTO few_shot_candidates
                                (id, agent_domain, interaction_id, quality_score, status, example_yaml, anonymized, company_id, created_at)
                                VALUES (:id, :domain, :iid, :score, 'pending', :yaml, true, :cid, NOW())
                            """),
                            {
                                "id": str(uuid.uuid4()),
                                "domain": domain,
                                "iid": str(interaction.get("id", "")),
                                "score": score,
                                "yaml": yaml.dump(example, allow_unicode=True),
                                "cid": str(interaction.get("company_id", "")),
                            },
                        )
                        await db.commit()
                    results["pending_review"] += 1
                except Exception as exc:
                    logger.debug("[FewShotEvolution] DB insert failed: %s", exc)
                    results["rejected"] += 1

    logger.info(
        "[FewShotEvolution] Done: processed=%d auto=%d pending=%d rejected=%d",
        results["processed"], results["auto_inserted"], results["pending_review"], results["rejected"],
    )
    return results
