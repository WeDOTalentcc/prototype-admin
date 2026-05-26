"""
Golden Scenario Drift Monitor — qualitative drift detection via eval framework.

Complements the quantitative ModelDriftService (score/approval/cost/latency)
with qualitative checks: runs golden scenarios periodically, compares with
saved baseline, and classifies drift as STABLE/WARNING/CRITICAL.

Item: P37-073 — Sprint 11, item 11.3
Depends on: 6.1 (eval runner), 6.2 (golden scenarios), 10.1 (dashboard)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_EVAL_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "eval"
_BASELINE_PATH = _EVAL_DIR / "baseline_scores.json"

# Drift thresholds (percentage drop from baseline)
DRIFT_THRESHOLD_WARNING = 0.05   # 5% drop
DRIFT_THRESHOLD_CRITICAL = 0.15  # 15% drop

AGENTS_TO_MONITOR = ["screening", "sourcing", "pipeline", "wizard", "communication"]


# ── Data structures ──────────────────────────────────────────────

@dataclass
class AgentBaseline:
    agent: str
    pass_rate: float  # 0.0-1.0
    avg_score: float  # from suite results
    updated_at: str = ""


@dataclass
class AgentDriftResult:
    agent: str
    baseline_pass_rate: float
    current_pass_rate: float
    delta: float  # negative = degradation
    status: str  # "stable" | "warning" | "critical" | "no_baseline"


@dataclass
class DriftReport:
    timestamp: str
    agents: list[AgentDriftResult] = field(default_factory=list)
    overall_status: str = "stable"  # worst status across all agents
    eval_errors: list[str] = field(default_factory=list)


# ── Baseline Manager ─────────────────────────────────────────────

class BaselineManager:
    """Persist and load golden scenario baselines as JSON file."""

    def __init__(self, path: Path = _BASELINE_PATH):
        self._path = path

    def load(self) -> dict[str, AgentBaseline]:
        """Load baseline from disk. Returns empty dict if no baseline exists."""
        if not self._path.exists():
            return {}
        try:
            with open(self._path) as f:
                data = json.load(f)
            return {
                name: AgentBaseline(**vals)
                for name, vals in data.get("agents", {}).items()
            }
        except Exception as exc:
            logger.warning("[BaselineManager] Failed to load baseline: %s", exc)
            return {}

    def save(self, baselines: dict[str, AgentBaseline]) -> None:
        """Save baseline to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "baseline_date": datetime.now(timezone.utc).isoformat(),
            "agents": {name: asdict(b) for name, b in baselines.items()},
        }
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("[BaselineManager] Saved baseline for %d agents", len(baselines))

    def has_baseline(self) -> bool:
        return self._path.exists()


# ── Golden Drift Detector ────────────────────────────────────────

class GoldenDriftDetector:
    """Run golden scenarios and compare with baseline."""

    def __init__(self):
        self._baseline_mgr = BaselineManager()

    def run_check(self) -> DriftReport:
        """
        Run golden scenarios for all monitored agents, compare with baseline.

        If no baseline exists, generates one from this run (first-time setup).
        """
        report = DriftReport(timestamp=datetime.now(timezone.utc).isoformat())

        # Run golden eval programmatically
        try:
            from tests.eval.runner import run_eval
            eval_result = run_eval(suite="golden", dry_run=False)
        except Exception as exc:
            logger.error("[GoldenDrift] Eval runner failed: %s", exc)
            report.eval_errors.append(str(exc))
            report.overall_status = "error"
            return report

        # Extract pass rates from eval result
        current_scores = self._extract_scores(eval_result)

        # Load baseline
        baselines = self._baseline_mgr.load()

        if not baselines:
            # First run — save current as baseline
            new_baselines = {
                agent: AgentBaseline(
                    agent=agent,
                    pass_rate=scores.get("pass_rate", 0.0),
                    avg_score=scores.get("avg_score", 0.0),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
                for agent, scores in current_scores.items()
            }
            self._baseline_mgr.save(new_baselines)
            logger.info("[GoldenDrift] No baseline found — created from this run")
            report.overall_status = "baseline_created"
            return report

        # Compare current vs baseline
        worst_status = "stable"

        for agent in AGENTS_TO_MONITOR:
            baseline = baselines.get(agent)
            current = current_scores.get(agent, {})

            if not baseline:
                report.agents.append(AgentDriftResult(
                    agent=agent,
                    baseline_pass_rate=0.0,
                    current_pass_rate=current.get("pass_rate", 0.0),
                    delta=0.0,
                    status="no_baseline",
                ))
                continue

            current_rate = current.get("pass_rate", 0.0)
            baseline_rate = baseline.pass_rate

            if baseline_rate > 0:
                delta = (current_rate - baseline_rate) / baseline_rate
            else:
                delta = 0.0

            if delta <= -DRIFT_THRESHOLD_CRITICAL:
                status = "critical"
            elif delta <= -DRIFT_THRESHOLD_WARNING:
                status = "warning"
            else:
                status = "stable"

            report.agents.append(AgentDriftResult(
                agent=agent,
                baseline_pass_rate=round(baseline_rate, 3),
                current_pass_rate=round(current_rate, 3),
                delta=round(delta, 4),
                status=status,
            ))

            # Track worst
            if status == "critical":
                worst_status = "critical"
            elif status == "warning" and worst_status != "critical":
                worst_status = "warning"

        report.overall_status = worst_status
        return report

    def _extract_scores(self, eval_result: dict) -> dict[str, dict[str, float]]:
        """Extract per-agent scores from eval runner output."""
        scores: dict[str, dict[str, float]] = {}
        golden = eval_result.get("suites", {}).get("golden", {})
        results = golden.get("results", [])

        passed_count = sum(1 for r in results if r.get("passed"))
        total_count = max(len(results), 1)
        global_pass_rate = passed_count / total_count

        # Assign global rate to all agents (eval runner doesn't split per-agent yet)
        for agent in AGENTS_TO_MONITOR:
            scores[agent] = {
                "pass_rate": global_pass_rate,
                "avg_score": global_pass_rate * 10,  # normalized
            }

        return scores

    def update_baseline(self) -> dict[str, Any]:
        """Force-update baseline from current golden run."""
        try:
            from tests.eval.runner import run_eval
            eval_result = run_eval(suite="golden", dry_run=False)
        except Exception as exc:
            return {"error": str(exc)}

        current_scores = self._extract_scores(eval_result)
        new_baselines = {
            agent: AgentBaseline(
                agent=agent,
                pass_rate=scores.get("pass_rate", 0.0),
                avg_score=scores.get("avg_score", 0.0),
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            for agent, scores in current_scores.items()
        }
        self._baseline_mgr.save(new_baselines)
        return {"status": "baseline_updated", "agents": list(new_baselines.keys())}


# ── Alert dispatcher ─────────────────────────────────────────────

def dispatch_drift_alerts(report: DriftReport) -> None:
    """Send alerts for WARNING/CRITICAL drift results.

    Sprint 7C Part 1.5b/c: audit dim 5 canonical wired (feature-audit).
    """
    try:
        # Audit dim 5 — emit log_decision canonical pra trail.
        # Sync function: usar asyncio.run via best-effort (sem bloquear flow se loop em uso).
        import asyncio as _asyncio_audit
        from app.shared.compliance.audit_service import AuditService as _AuditAudit
        _critical_agents = [a.agent for a in report.agents if a.status == "critical"]
        _warn_agents = [a.agent for a in report.agents if a.status == "warning"]
        if _critical_agents or _warn_agents:
            async def _audit_drift():
                _svc = _AuditAudit()
                await _svc.log_decision(
                    company_id="__system__",
                    agent_name="golden_drift_monitor",
                    decision_type="dispatch",
                    action="dispatch_drift_alerts",
                    decision="executed",
                    reasoning=[
                        f"critical={_critical_agents}",
                        f"warning={_warn_agents}",
                    ],
                    criteria_used=[],
                )
            try:
                _asyncio_audit.run(_audit_drift())
            except RuntimeError:
                pass  # event loop ja rodando — skip audit best-effort
    except Exception:
        pass  # audit best-effort, nao bloqueia alerts
    for agent_result in report.agents:
        if agent_result.status == "critical":
            msg = (
                f"CRITICAL: Agente {agent_result.agent} degradou "
                f"{abs(agent_result.delta):.0%} nos golden scenarios. "
                f"Baseline: {agent_result.baseline_pass_rate:.0%}, "
                f"Atual: {agent_result.current_pass_rate:.0%}."
            )
            logger.critical("[GoldenDrift] %s", msg)
            _send_sentry_alert(msg, level="error")

        elif agent_result.status == "warning":
            msg = (
                f"WARNING: Agente {agent_result.agent} degradou "
                f"{abs(agent_result.delta):.0%} nos golden scenarios. "
                f"Baseline: {agent_result.baseline_pass_rate:.0%}, "
                f"Atual: {agent_result.current_pass_rate:.0%}."
            )
            logger.warning("[GoldenDrift] %s", msg)
            _send_sentry_alert(msg, level="warning")


def _send_sentry_alert(message: str, level: str = "warning") -> None:
    """Send alert to Sentry if configured."""
    try:
        import sentry_sdk
        if level == "error":
            sentry_sdk.capture_message(message, level="error")
        else:
            sentry_sdk.capture_message(message, level="warning")
    except Exception:
        pass  # Sentry not available — already logged above


# Singleton
golden_drift_detector = GoldenDriftDetector()
