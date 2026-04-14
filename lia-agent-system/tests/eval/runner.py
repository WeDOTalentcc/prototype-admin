"""
Eval Runner — centralized orchestrator for all evaluation suites.

Delegates to existing frameworks (DeepEval, RAGAS, governance) without
duplicating them. Provides unified CLI, config, and result aggregation.

Usage:
    python -m tests.eval.runner --suite unit
    python -m tests.eval.runner --suite golden --agent screening
    python -m tests.eval.runner --suite bias --dry-run
    python -m tests.eval.runner --suite all
    python -m tests.eval.runner --suite all --output results/run_2026-04-14.json
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent  # lia-agent-system/
_EVAL_DIR = Path(__file__).resolve().parent  # tests/eval/
_CONFIG_PATH = _EVAL_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    """Load eval config YAML."""
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _run_pytest(test_path: str, extra_args: list[str] | None = None, timeout: int = 300) -> dict:
    """Run a pytest suite and capture results."""
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v", "--tb=short", "--no-cov", "--no-header",
        f"--timeout={timeout}",
    ]
    if extra_args:
        cmd.extend(extra_args)

    start = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout + 30,
            cwd=str(_ROOT),
        )
        duration = time.time() - start
        passed = result.returncode == 0
        return {
            "passed": passed,
            "returncode": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout_tail": result.stdout[-2000:] if result.stdout else "",
            "stderr_tail": result.stderr[-500:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "returncode": -1,
            "duration_seconds": timeout,
            "stdout_tail": "",
            "stderr_tail": f"TIMEOUT after {timeout}s",
        }


# ---------------------------------------------------------------------------
# Suite runners — delegate to existing frameworks
# ---------------------------------------------------------------------------

def run_unit_suite(config: dict, agent: str | None = None, dry_run: bool = False) -> dict:
    """Run unit evals — fast deterministic checks per agent."""
    suites_cfg = config.get("suites", {}).get("unit", {})
    test_paths = ["tests/fitness/"]  # fitness functions are our unit architectural evals

    if dry_run:
        return {"suite": "unit", "dry_run": True, "would_run": test_paths}

    results = []
    for path in test_paths:
        full_path = str(_ROOT / path)
        results.append({"path": path, **_run_pytest(full_path)})

    all_passed = all(r["passed"] for r in results)
    return {
        "suite": "unit",
        "passed": all_passed,
        "thresholds": suites_cfg.get("thresholds", {}),
        "results": results,
    }


def run_golden_suite(config: dict, agent: str | None = None, dry_run: bool = False) -> dict:
    """Run golden scenario evals — delegates to RAGAS + quality_suite."""
    suites_cfg = config.get("suites", {}).get("golden", {})
    test_paths = [
        "tests/ragas/",
        "tests/quality_suite/test_ragas_evaluation.py",
    ]

    if agent:
        agent_cfg = config.get("agents", {}).get(agent, {})
        ds = agent_cfg.get("golden_dataset")
        if ds:
            ds_path = _EVAL_DIR / ds
            if ds_path.exists():
                test_paths.append(str(ds_path))

    if dry_run:
        return {"suite": "golden", "dry_run": True, "would_run": test_paths, "agent_filter": agent}

    results = []
    for path in test_paths:
        full_path = str(_ROOT / path) if not Path(path).is_absolute() else path
        results.append({"path": path, **_run_pytest(full_path, timeout=120)})

    all_passed = all(r["passed"] for r in results)
    return {
        "suite": "golden",
        "passed": all_passed,
        "thresholds": suites_cfg.get("thresholds", {}),
        "agent_filter": agent,
        "results": results,
    }


def run_bias_suite(config: dict, agent: str | None = None, dry_run: bool = False) -> dict:
    """Run bias probes — delegates to fairness tests + governance."""
    suites_cfg = config.get("suites", {}).get("bias", {})
    test_paths = [
        "tests/fairness/",
        "tests/quality_suite/test_governance_expanded.py",
    ]

    if dry_run:
        return {"suite": "bias", "dry_run": True, "would_run": test_paths}

    results = []
    for path in test_paths:
        full_path = str(_ROOT / path)
        results.append({"path": path, **_run_pytest(full_path, timeout=120)})

    all_passed = all(r["passed"] for r in results)
    return {
        "suite": "bias",
        "passed": all_passed,
        "thresholds": suites_cfg.get("thresholds", {}),
        "results": results,
    }


def run_integration_suite(config: dict, agent: str | None = None, dry_run: bool = False) -> dict:
    """Run integration evals — cross-agent handoffs."""
    suites_cfg = config.get("suites", {}).get("integration", {})
    test_paths = [
        "tests/integration/",
        "tests/deepeval/",
    ]

    if dry_run:
        return {"suite": "integration", "dry_run": True, "would_run": test_paths}

    results = []
    for path in test_paths:
        full_path = str(_ROOT / path)
        results.append({"path": path, **_run_pytest(full_path, timeout=180)})

    all_passed = all(r["passed"] for r in results)
    return {
        "suite": "integration",
        "passed": all_passed,
        "thresholds": suites_cfg.get("thresholds", {}),
        "results": results,
    }


def run_adversarial_suite(config: dict, agent: str | None = None, dry_run: bool = False) -> dict:
    """Run adversarial attack scenarios — delegates to governance + security tests."""
    suites_cfg = config.get("suites", {}).get("adversarial", {})
    test_paths = [
        "tests/quality_suite/test_governance_expanded.py",
        "tests/security/",
    ]

    # Include adversarial dataset info in dry-run
    adversarial_yaml = _EVAL_DIR / "datasets" / "adversarial" / "attack_scenarios.yaml"
    scenario_count = 0
    if adversarial_yaml.exists():
        try:
            with open(adversarial_yaml) as f:
                data = yaml.safe_load(f)
                scenario_count = len(data.get("scenarios", []))
        except Exception:
            pass

    if dry_run:
        return {
            "suite": "adversarial",
            "dry_run": True,
            "would_run": test_paths,
            "attack_scenarios": scenario_count,
            "severity_breakdown": {"critical": 5, "high": 3},
        }

    results = []
    for path in test_paths:
        full_path = str(_ROOT / path)
        results.append({"path": path, **_run_pytest(full_path, timeout=120)})

    all_passed = all(r["passed"] for r in results)
    return {
        "suite": "adversarial",
        "passed": all_passed,
        "thresholds": suites_cfg.get("thresholds", {}),
        "attack_scenarios": scenario_count,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

_SUITE_RUNNERS = {
    "unit": run_unit_suite,
    "golden": run_golden_suite,
    "bias": run_bias_suite,
    "adversarial": run_adversarial_suite,
    "integration": run_integration_suite,
}


def run_eval(suite: str, agent: str | None = None, dry_run: bool = False, output: str | None = None) -> dict:
    """Run one or all eval suites."""
    config = load_config()
    start_time = datetime.now(timezone.utc)

    if suite == "all":
        suites_to_run = list(_SUITE_RUNNERS.keys())
    else:
        suites_to_run = [suite]

    results = {}
    overall_passed = True

    for suite_name in suites_to_run:
        runner = _SUITE_RUNNERS.get(suite_name)
        if not runner:
            results[suite_name] = {"error": f"Unknown suite: {suite_name}"}
            overall_passed = False
            continue

        print(f"\n{'='*60}")
        print(f"Running suite: {suite_name}" + (f" (agent={agent})" if agent else ""))
        print(f"{'='*60}")

        suite_result = runner(config, agent=agent, dry_run=dry_run)
        results[suite_name] = suite_result

        if not suite_result.get("passed", False) and not dry_run:
            overall_passed = False

        status = "PASS" if suite_result.get("passed") else ("DRY-RUN" if dry_run else "FAIL")
        print(f"  → {suite_name}: {status}")

    report = {
        "generated_at": start_time.isoformat(),
        "suite_requested": suite,
        "agent_filter": agent,
        "dry_run": dry_run,
        "overall_passed": overall_passed,
        "suites": results,
    }

    # Save results
    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = _EVAL_DIR / output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nResults saved to: {output_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"EVAL SUMMARY: {'PASS' if overall_passed else 'FAIL'}")
    for name, res in results.items():
        status = "PASS" if res.get("passed") else ("DRY-RUN" if dry_run else "FAIL")
        print(f"  {name}: {status}")
    print(f"{'='*60}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LIA Eval Runner — run evaluation suites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m tests.eval.runner --suite unit
  python -m tests.eval.runner --suite golden --agent screening
  python -m tests.eval.runner --suite bias --dry-run
  python -m tests.eval.runner --suite all --output results/run.json
        """,
    )
    parser.add_argument("--suite", required=True, choices=["unit", "golden", "bias", "adversarial", "integration", "all"])
    parser.add_argument("--agent", help="Filter by agent (screening, sourcing, pipeline, wizard, communication)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without executing")
    parser.add_argument("--output", help="Save results to JSON file (relative to tests/eval/ or absolute)")
    parser.add_argument("--threshold", type=float, help="Override minimum pass threshold")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    report = run_eval(
        suite=args.suite,
        agent=args.agent,
        dry_run=args.dry_run,
        output=args.output,
    )

    sys.exit(0 if report["overall_passed"] else 1)


if __name__ == "__main__":
    main()
