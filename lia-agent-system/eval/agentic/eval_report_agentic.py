"""HTML report generator for the agentic eval roteiro.

Builds on the design of ``eval_report.py`` but renders the 10-dimension
scorecard, per-scenario heatmap, tool-call diff, and pass^k overlay.

Usage:
    python lia-agent-system/eval/agentic/eval_report_agentic.py \
        runs/agentic-<TS>_judged.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DIMENSIONS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"]
DIM_NAMES = {
    "D1": "Memory", "D2": "Self-know", "D3": "Grounding", "D4": "Planning",
    "D5": "Clarify", "D6": "Robustness", "D7": "Sensitive", "D8": "Refusal",
    "D9": "pass^k", "D10": "Proactive",
}


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def color_for(score: float | None) -> str:
    if score is None:
        return "#7a82a0"
    if score >= 2.5:
        return "#27ae60"
    if score >= 2.0:
        return "#2ecc71"
    if score >= 1.0:
        return "#e67e22"
    return "#e74c3c"


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def load_previous(in_path: Path) -> dict | None:
    """Find the most recent ``*_judged.json`` sibling that is older than ``in_path``."""
    siblings = sorted(
        (p for p in in_path.parent.glob("*_judged.json") if p != in_path),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for s in siblings:
        if s.stat().st_mtime < in_path.stat().st_mtime:
            try:
                return {"path": s.name, "payload": json.loads(s.read_text(encoding="utf-8"))}
            except Exception:
                continue
    return None


def per_dim_avg(payload: dict) -> dict[str, float | None]:
    scores: dict[str, list[int]] = defaultdict(list)
    pass_k = payload.get("pass_k", {}) or {}
    for cap in payload.get("results", []):
        j = cap.get("judgment", {}) or {}
        for d, s in (j.get("scores") or {}).items():
            if s is not None:
                scores[d].append(s)
        sid = cap.get("scenario_id")
        if sid in pass_k and pass_k[sid].get("D9") is not None:
            scores["D9"].append(pass_k[sid]["D9"])
    return {d: (sum(v) / len(v)) if v else None for d, v in scores.items()}


def build_html(payload: dict, source: str, previous: dict | None = None) -> str:
    captures = payload.get("results", [])
    pass_k = payload.get("pass_k", {})
    run_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # ── per-dimension aggregates ──────────────────────────────────────
    dim_scores: dict[str, list[int]] = defaultdict(list)
    crit_count = 0
    for cap in captures:
        j = cap.get("judgment", {}) or {}
        if j.get("critical_failure"):
            crit_count += 1
        for d, s in (j.get("scores") or {}).items():
            if s is not None:
                dim_scores[d].append(s)
        if cap.get("scenario_id") in pass_k:
            d9 = pass_k[cap["scenario_id"]].get("D9")
            if d9 is not None:
                dim_scores["D9"].append(d9)

    dim_avg = {d: (sum(v) / len(v)) if v else None for d, v in dim_scores.items()}
    dim_pass = {d: (sum(1 for s in v if s >= 2) / len(v) * 100) if v else None for d, v in dim_scores.items()}

    overall = [a for a in dim_avg.values() if a is not None]
    overall_avg = round(sum(overall) / len(overall), 2) if overall else 0
    decision_color = "#27ae60"
    decision_text = "SHIP"
    if crit_count > 0:
        decision_color, decision_text = "#e74c3c", f"BLOCK — {crit_count} critical failure(s)"
    elif any((a or 0) < 2.0 for a in dim_avg.values() if a is not None):
        decision_color, decision_text = "#e74c3c", "BLOCK — dimension below 2.0"
    elif any((a or 0) < 2.5 for a in dim_avg.values() if a is not None):
        decision_color, decision_text = "#e67e22", "SHIP WITH NOTE"

    # ── dimension cards ───────────────────────────────────────────────
    dim_cards = ""
    for d in DIMENSIONS:
        avg = dim_avg.get(d)
        pct = dim_pass.get(d)
        c = color_for(avg)
        avg_s = f"{avg:.2f}" if avg is not None else "—"
        pct_s = f"{pct:.0f}%" if pct is not None else "—"
        dim_cards += (
            '<div class="dim-card">'
            f'<div class="dim-id">{d}</div>'
            f'<div class="dim-name">{DIM_NAMES[d]}</div>'
            f'<div class="dim-avg" style="color:{c}">{avg_s}</div>'
            f'<div class="dim-pct">{pct_s} pass</div>'
            '</div>'
        )

    # ── scenario rows ─────────────────────────────────────────────────
    rows = ""
    for cap in captures:
        sid = cap.get("scenario_id", "?")
        j = cap.get("judgment") or {}
        scores = j.get("scores") or {}
        crit = j.get("critical_failure")
        cells = ""
        for d in DIMENSIONS:
            if d == "D9":
                s = pass_k.get(sid, {}).get("D9")
            else:
                s = scores.get(d)
            cells += f'<td class="cell" style="background:{color_for(s)}">{"—" if s is None else s}</td>'
        crit_badge = '<span class="crit">⚠ CRITICAL</span>' if crit else ''
        summary = esc((j.get("summary") or "")[:200])
        rows += (
            f'<tr><td class="sid">{esc(sid)}</td>'
            f'<td>{esc(", ".join(cap.get("tags", [])))}</td>'
            f'{cells}'
            f'<td class="summary">{summary}{crit_badge}</td>'
            '</tr>'
        )

    # ── regression vs previous run ────────────────────────────────────
    regression_html = ""
    if previous:
        prev_avg = per_dim_avg(previous["payload"])
        reg_rows = ""
        for d in DIMENSIONS:
            cur = dim_avg.get(d)
            prv = prev_avg.get(d)
            if cur is None and prv is None:
                continue
            cur_s = f"{cur:.2f}" if cur is not None else "—"
            prv_s = f"{prv:.2f}" if prv is not None else "—"
            if cur is not None and prv is not None:
                delta = cur - prv
                arrow = "▲" if delta > 0.05 else ("▼" if delta < -0.05 else "•")
                col = "#27ae60" if delta > 0.05 else ("#e74c3c" if delta < -0.05 else "#7a82a0")
                delta_html = f'<span style="color:{col};font-weight:700">{arrow} {delta:+.2f}</span>'
            else:
                delta_html = '<span style="color:#7a82a0">—</span>'
            reg_rows += f'<tr><td class="sid">{d}</td><td>{prv_s}</td><td>{cur_s}</td><td>{delta_html}</td></tr>'
        regression_html = (
            '<h2>Regression vs previous run</h2>'
            f'<div class="meta">Previous: {esc(previous["path"])}</div>'
            '<table><thead><tr><th>Dim</th><th>Previous avg</th><th>Current avg</th><th>Δ</th></tr></thead>'
            f'<tbody>{reg_rows}</tbody></table>'
        )
    else:
        regression_html = (
            '<h2>Regression vs previous run</h2>'
            '<div class="meta" style="padding:12px 0">No prior judged run found in this folder — this is the baseline.</div>'
        )

    # ── top-N failures by severity ────────────────────────────────────
    failures: list[tuple[int, int, str, str, str]] = []  # (sev_rank, score, sid, severity, summary)
    for cap in captures:
        j = cap.get("judgment", {}) or {}
        scores = [s for s in (j.get("scores") or {}).values() if s is not None]
        if not scores:
            continue
        worst = min(scores)
        critical = j.get("critical_failure")
        sev = (cap.get("severity") or "medium").lower()
        if critical or worst <= 1:
            failures.append((
                SEVERITY_RANK.get(sev, 9),
                worst,
                cap.get("scenario_id", "?"),
                sev,
                (j.get("summary") or "")[:200],
            ))
    failures.sort(key=lambda r: (r[0], r[1]))
    top_n = failures[:10]
    if top_n:
        fail_rows = "".join(
            f'<tr><td class="sid">{esc(sid)}</td>'
            f'<td><span style="background:{"#e74c3c" if sev=="critical" else "#e67e22" if sev=="high" else "#7a82a0"};color:#fff;padding:1px 6px;border-radius:3px">{sev.upper()}</span></td>'
            f'<td style="color:{color_for(score)};font-weight:700">{score}</td>'
            f'<td class="summary">{esc(summary)}</td></tr>'
            for _, score, sid, sev, summary in top_n
        )
    else:
        fail_rows = '<tr><td colspan="4" style="color:var(--muted);padding:12px">No failures detected — all scenarios scored above 1.</td></tr>'
    failures_html = (
        f'<h2>Top {len(top_n)} failures by severity</h2>'
        '<table><thead><tr><th>Scenario</th><th>Severity</th><th>Worst score</th><th>Summary</th></tr></thead>'
        f'<tbody>{fail_rows}</tbody></table>'
    )

    # ── tool-call diff table ──────────────────────────────────────────
    tool_rows = ""
    for cap in captures:
        sid = cap.get("scenario_id", "?")
        expected = set(cap.get("expected_tools") or [])
        observed = {t.get("name") for t in (cap.get("observed_tools") or []) if t.get("name")}
        if not (expected or observed):
            continue
        missing = expected - observed
        unexpected = observed - expected
        ok = expected and not missing and not unexpected
        status = "✓" if ok else ("~" if not missing else "✗")
        color = "#2ecc71" if ok else ("#e67e22" if not missing else "#e74c3c")
        tool_rows += (
            f'<tr><td class="sid">{esc(sid)}</td>'
            f'<td style="color:{color}">{status}</td>'
            f'<td>{esc(", ".join(sorted(expected)) or "—")}</td>'
            f'<td>{esc(", ".join(sorted(observed)) or "—")}</td>'
            f'<td style="color:#e74c3c">{esc(", ".join(sorted(missing)) or "—")}</td>'
            f'<td style="color:#3498db">{esc(", ".join(sorted(unexpected)) or "—")}</td>'
            '</tr>'
        )

    css = """
:root{--bg:#0f1117;--bg2:#1a1d26;--bg3:#22263a;--border:#2d3148;--text:#e0e4f0;--muted:#7a82a0}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);padding:24px;font-size:13px}
h1{font-size:24px;font-weight:700;margin-bottom:6px}
h2{font-size:15px;color:var(--muted);margin:24px 0 12px;text-transform:uppercase;letter-spacing:0.5px}
.meta{color:var(--muted);font-size:12px;margin-bottom:20px}
.decision{padding:14px 24px;border-radius:10px;display:inline-block;font-weight:700;font-size:18px;color:#fff;margin-bottom:24px}
.summary-bar{display:flex;gap:14px;margin-bottom:24px;flex-wrap:wrap}
.stat{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px 22px;min-width:120px;text-align:center}
.stat-val{font-size:26px;font-weight:700}
.stat-lbl{font-size:11px;color:var(--muted);text-transform:uppercase;margin-top:4px}
.dim-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:10px;margin-bottom:28px}
.dim-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 10px;text-align:center}
.dim-id{font-family:monospace;font-weight:700;font-size:12px;color:var(--muted)}
.dim-name{font-size:11px;color:var(--muted);margin-top:2px}
.dim-avg{font-size:22px;font-weight:700;margin-top:6px}
.dim-pct{font-size:10px;color:var(--muted);margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:var(--bg3);padding:6px 8px;text-align:left;color:var(--muted);text-transform:uppercase;font-size:10px;border-bottom:2px solid var(--border)}
td{padding:5px 8px;border-bottom:1px solid var(--border);vertical-align:top}
.cell{text-align:center;color:#fff;font-weight:700;width:32px}
.sid{font-family:monospace;font-weight:700}
.summary{color:var(--muted);font-size:11px;max-width:380px}
.crit{display:inline-block;background:#e74c3c;color:#fff;padding:1px 6px;border-radius:3px;margin-left:6px;font-size:10px}
.heat-table{margin-bottom:32px}
"""

    return (
        '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">'
        f'<title>LIA Agentic Eval — {run_date}</title>'
        f'<style>{css}</style></head><body>'
        f'<h1>LIA Agentic Eval Report</h1>'
        f'<div class="meta">Generated {run_date} — Source: {esc(source)}</div>'
        f'<div class="decision" style="background:{decision_color}">{decision_text}</div>'
        '<div class="summary-bar">'
        f'<div class="stat"><div class="stat-val">{overall_avg}</div><div class="stat-lbl">Overall avg</div></div>'
        f'<div class="stat"><div class="stat-val">{len(captures)}</div><div class="stat-lbl">Scenarios</div></div>'
        f'<div class="stat"><div class="stat-val" style="color:#e74c3c">{crit_count}</div><div class="stat-lbl">Critical fails</div></div>'
        f'<div class="stat"><div class="stat-val">{len(pass_k)}</div><div class="stat-lbl">pass^k tracked</div></div>'
        '</div>'
        '<h2>Per-dimension scorecard</h2>'
        f'<div class="dim-grid">{dim_cards}</div>'
        '<h2>Scenario × dimension heatmap</h2>'
        '<div class="heat-table"><table><thead><tr><th>Scenario</th><th>Tags</th>'
        + ''.join(f'<th>{d}</th>' for d in DIMENSIONS)
        + '<th>Summary</th></tr></thead><tbody>'
        + rows
        + '</tbody></table></div>'
        + failures_html
        + regression_html
        + '<h2>Tool-call diff (expected vs. observed)</h2>'
        '<table><thead><tr><th>Scenario</th><th>OK</th><th>Expected</th><th>Observed</th><th>Missing</th><th>Unexpected</th></tr></thead><tbody>'
        + (tool_rows or '<tr><td colspan="6" style="color:var(--muted);padding:12px">No tool data captured</td></tr>')
        + '</tbody></table>'
        '</body></html>'
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Eval HTML Report")
    parser.add_argument("results_file", help="*_judged.json file from judge_agentic.py")
    args = parser.parse_args()

    in_path = Path(args.results_file)
    if not in_path.exists():
        raise SystemExit(f"File not found: {in_path}")

    payload = json.loads(in_path.read_text(encoding="utf-8"))
    previous = load_previous(in_path)
    html = build_html(payload, in_path.name, previous=previous)
    if previous:
        print(f"Regression baseline: {previous['path']}")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = in_path.parent / f"agentic_report_{ts}.html"
    out.write_text(html, encoding="utf-8")
    print(f"\nHTML report: {out}")


if __name__ == "__main__":
    main()
