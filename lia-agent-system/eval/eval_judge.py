#!/usr/bin/env python3
"""
LIA Eval Judge — LLM-as-judge using Claude
Re-scores results from eval_runner.py with deeper semantic analysis.

Usage:
  python eval_judge.py eval_results_<timestamp>.json [--rewrite]

Requires: ANTHROPIC_API_KEY env var
Output: eval_results_<timestamp>_judged.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

JUDGE_PROMPT = """\
You are an expert QA engineer evaluating an enterprise AI recruiting assistant called LIA.

# Test Case
ID: {case_id}
Category: {category}
Severity: {severity}
Title: {title}

# User Prompt
{prompt}

# Page Context
scope: {scope}
entity_id: {entity_id}

# Expected Behavior
{expected_behavior}

# Expected Tools to be Called
{expected_tools}

# Success Criteria
{success_criteria}

# Anti-Patterns to Detect
{anti_patterns}

# LIA's Actual Response
{response}

# Your Task
Score this response on a 0-3 scale:
- 0 = FAIL: Anti-pattern detected, tool not called, refused to act, or empty
- 1 = PARTIAL: Attempted but missed key criteria or took wrong approach
- 2 = PASS: Met main success criteria, no critical anti-patterns
- 3 = PERFECT: All criteria met, proactive, correct tool use, professional tone

Respond ONLY with valid JSON:
{{
  "score": <0|1|2|3>,
  "verdict": "<FAIL|PARTIAL|PASS|PERFECT>",
  "tool_called_correctly": <true|false|null>,
  "context_used": <true|false>,
  "confirmation_requested": <true|false|null>,
  "anti_pattern_detected": "<description or null>",
  "reasoning": "<1-2 sentence explanation>",
  "suggested_fix": "<which canonical file to fix, or null>"
}}
"""


def judge_with_claude(case_result: dict) -> dict[str, Any]:
    try:
        import anthropic
    except ImportError:
        return {"score": case_result["score"], "verdict": "HEURISTIC_ONLY", "error": "anthropic not installed"}

    if not ANTHROPIC_API_KEY:
        return {"score": case_result["score"], "verdict": "HEURISTIC_ONLY", "error": "no ANTHROPIC_API_KEY"}

    ctx = case_result.get("context", {})
    prompt = JUDGE_PROMPT.format(
        case_id=case_result["id"],
        category=case_result["category"],
        severity=case_result["severity"],
        title=case_result["title"],
        prompt=case_result["prompt"],
        scope=ctx.get("scope", "global"),
        entity_id=ctx.get("entity_id", "none"),
        expected_behavior="\n".join(f"- {c}" for c in case_result.get("success_criteria", [])),
        expected_tools=", ".join(case_result.get("expected_tools", [])) or "none",
        success_criteria="\n".join(f"- {c}" for c in case_result.get("success_criteria", [])),
        anti_patterns="\n".join(f"- {ap}" for ap in case_result.get("anti_patterns", [])),
        response=case_result.get("response", "(empty)"),
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        # Extract JSON from response
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        judgment = json.loads(raw)
        judgment["judged_by"] = "claude-haiku"
        return judgment
    except Exception as exc:
        return {
            "score": case_result["score"],
            "verdict": "JUDGE_ERROR",
            "error": str(exc),
            "judged_by": "none",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="LIA Eval Judge")
    parser.add_argument("results_file", help="eval_results_*.json file from eval_runner.py")
    parser.add_argument("--rewrite", action="store_true", help="Overwrite scores with judge scores")
    parser.add_argument("--filter-fails", action="store_true", help="Only judge failed cases (score <= 1)")
    args = parser.parse_args()

    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"File not found: {results_path}")
        sys.exit(1)

    results = json.loads(results_path.read_text())
    to_judge = [r for r in results if r["score"] <= 1] if args.filter_fails else results

    print(f"\nJudging {len(to_judge)}/{len(results)} cases with Claude Haiku...\n")

    judged = 0
    for i, result in enumerate(results):
        if result not in to_judge:
            result["judgment"] = {"score": result["score"], "verdict": "SKIPPED", "judged_by": "none"}
            continue

        print(f"  [{i+1:02d}] {result['id']:<10} {result['title'][:40]}", end="", flush=True)
        judgment = judge_with_claude(result)
        result["judgment"] = judgment

        if args.rewrite:
            result["score"] = judgment.get("score", result["score"])

        verdict = judgment.get("verdict", "?")
        icon = {"FAIL": "✗", "PARTIAL": "~", "PASS": "✓", "PERFECT": "★"}.get(verdict, "?")
        print(f"  {icon} {verdict}")
        judged += 1

        # Rate limiting
        time.sleep(0.3)

    # Summary
    judged_scores = [r["judgment"]["score"] for r in results if "judgment" in r and r["judgment"].get("judged_by") != "none"]
    if judged_scores:
        avg = sum(judged_scores) / len(judged_scores)
        passed = sum(1 for s in judged_scores if s >= 2)
        print(f"\n  Judged: {judged} cases")
        print(f"  Pass rate: {passed}/{len(judged_scores)} ({100*passed//len(judged_scores)}%)")
        print(f"  Average score: {avg:.2f}/3.0")

    # Common failure patterns
    fails = [r for r in results if r.get("judgment", {}).get("score", 3) <= 1]
    if fails:
        print(f"\n  Top failure patterns:")
        file_counts: dict[str, int] = {}
        for r in fails:
            for f in r.get("canonical_files", []):
                file_counts[f] = file_counts.get(f, 0) + 1
        for f, count in sorted(file_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    {count}x {f}")

    # Save
    out_path = results_path.with_suffix("").with_suffix("_judged.json")
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n  Judged results saved: {out_path.name}")
    print(f"  Run eval_report.py {out_path.name} to generate HTML\n")


if __name__ == "__main__":
    main()
