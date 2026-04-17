#!/usr/bin/env python3
"""
LIA Eval Report — HTML visual report generator
Reads judged results and generates a self-contained HTML dashboard.

Usage:
  python eval_report.py eval_results_<timestamp>_judged.json
  python eval_report.py eval_results_<timestamp>.json

Output: eval_report_<timestamp>.html
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
CATEGORY_NAMES = {
    "JM": "Job Management", "CM": "Candidate Management", "KB": "Kanban / Pipeline",
    "SC": "Screening / WSI", "CO": "Communication", "AN": "Analytics / Reports",
    "SO": "Sourcing", "WZ": "Wizard / Job Creation", "PR": "Predictive / Proactive",
    "MT": "Multi-task Planning", "CX": "Context Awareness", "EX": "Edge Cases",
}
SCORE_COLORS = {0: "#e74c3c", 1: "#e67e22", 2: "#2ecc71", 3: "#27ae60"}
SCORE_LABELS = {0: "FAIL", 1: "PARTIAL", 2: "PASS", 3: "PERFECT"}
SCORE_ICONS  = {0: "✗", 1: "~", 2: "✓", 3: "★"}


def get_score(r: dict) -> int:
    return r.get("judgment", {}).get("score", r.get("score", 0))


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(results: list[dict], source_file: str) -> str:
    total   = len(results)
    passed  = sum(1 for r in results if get_score(r) >= 2)
    pass_pct = round(100 * passed / total) if total else 0
    critical_fails = [r for r in results if get_score(r) == 0 and r["severity"] == "critical"]

    by_cat: dict[str, list] = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)

    file_failures: dict[str, int] = defaultdict(int)
    for r in results:
        if get_score(r) <= 1:
            for f in r.get("canonical_files", []):
                file_failures[f] += 1

    run_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    score_color = "#2ecc71" if pass_pct >= 80 else ("#e67e22" if pass_pct >= 60 else "#e74c3c")

    # ── category cards ──
    cat_cards = ""
    for cat, cat_results in sorted(by_cat.items()):
        cat_passed = sum(1 for r in cat_results if get_score(r) >= 2)
        cat_pct = round(100 * cat_passed / len(cat_results)) if cat_results else 0
        bar_color = "#2ecc71" if cat_pct >= 80 else ("#e67e22" if cat_pct >= 50 else "#e74c3c")
        cat_name = CATEGORY_NAMES.get(cat, cat)
        cat_cards += (
            '<div class="cat-card">'
            '<div class="cat-header">'
            '<span class="cat-id">' + cat + '</span>'
            '<span class="cat-name">' + cat_name + '</span>'
            '<span class="cat-score" style="color:' + bar_color + '">' + str(cat_passed) + '/' + str(len(cat_results)) + '</span>'
            '</div>'
            '<div class="cat-bar-bg"><div class="cat-bar" style="width:' + str(cat_pct) + '%;background:' + bar_color + '"></div></div>'
            '<span class="cat-pct">' + str(cat_pct) + '%</span>'
            '</div>'
        )

    # ── result rows ──
    rows = ""
    for r in sorted(results, key=lambda x: (SEVERITY_ORDER.get(x["severity"], 9), x["id"])):
        score = get_score(r)
        color = SCORE_COLORS[score]
        label = SCORE_LABELS[score]
        icon  = SCORE_ICONS[score]
        sev_color = {"critical": "#e74c3c", "high": "#e67e22", "medium": "#3498db", "low": "#95a5a6"}[r["severity"]]
        judgment = r.get("judgment", {})
        reasoning = esc(judgment.get("reasoning", ""))
        fix       = esc(judgment.get("suggested_fix", "") or "")
        anti      = esc(judgment.get("anti_pattern_detected", "") or "")
        files_html = "".join('<code class="file">' + esc(f.split("/")[-1]) + '</code><br>' for f in r.get("canonical_files", []))
        flags_str  = esc(", ".join(r.get("flags", [])))
        resp_raw   = (r.get("response", "") or "")[:200]
        resp_html  = esc(resp_raw) + ("…" if len(r.get("response", "") or "") > 200 else "")
        err_html   = '<span class="error-badge">' + esc(r.get("error", "")[:60]) + '</span>' if r.get("error") else ""

        cell = ""
        if resp_html:
            cell += '<div class="response-preview">' + resp_html + '</div>'
        elif err_html:
            cell += err_html
        if reasoning:
            cell += '<div class="reasoning">' + reasoning + '</div>'
        if anti:
            cell += '<div class="anti-pattern">⚠ ' + anti + '</div>'
        if fix:
            cell += '<div class="fix-hint">🔧 ' + fix + '</div>'
        if flags_str:
            cell += '<div class="flags">' + flags_str + '</div>'

        rows += (
            '<tr class="row-' + label.lower() + '">'
            '<td><span class="case-id">' + r["id"] + '</span></td>'
            '<td><span class="sev-badge" style="background:' + sev_color + '">' + r["severity"][:4].upper() + '</span></td>'
            '<td class="title-cell">' + esc(r["title"]) + '</td>'
            '<td><span class="score-badge" style="background:' + color + '">' + icon + ' ' + label + '</span></td>'
            '<td class="lat-cell">' + str(r.get("latency_ms", -1)) + 'ms</td>'
            '<td class="files-cell">' + files_html + '</td>'
            '<td class="response-cell">' + cell + '</td>'
            '</tr>'
        )

    # ── file failure rows ──
    file_rows = ""
    for fpath, count in sorted(file_failures.items(), key=lambda x: -x[1])[:15]:
        fname = fpath.split("/")[-1]
        fdir  = "/".join(fpath.split("/")[:-1])
        file_rows += (
            '<tr>'
            '<td><code class="file">' + esc(fname) + '</code></td>'
            '<td class="dir-cell">' + esc(fdir) + '</td>'
            '<td><span class="fail-count">' + str(count) + '</span></td>'
            '</tr>'
        )
    if not file_rows:
        file_rows = '<tr><td colspan="3" style="color:var(--muted);padding:12px">No failures recorded</td></tr>'

    # ── critical failures block ──
    crit_block = ""
    if critical_fails:
        items = "".join(
            '<div class="critical-item">✗ <b>' + r["id"] + '</b> — ' + esc(r["title"]) +
            ' <span style="color:var(--muted);font-size:11px">(' + esc(", ".join(r.get("flags", [])[:1])) + ')</span></div>'
            for r in critical_fails
        )
        crit_block = '<div class="critical-block"><strong style="color:var(--red)">⚠ Critical Failures</strong>' + items + '</div>'

    # ── JS filter functions (plain string, no f-string) ──
    js = """
let activeSev = 'all';
let activeScore = null;
function filterRows() {
  const q = document.getElementById('search').value.toLowerCase();
  const rows = document.querySelectorAll('#resultsTable tbody tr');
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    const sevOk = activeSev === 'all' || text.includes(activeSev);
    const sOk   = activeScore === null || row.className.includes(['row-fail','row-partial','row-pass','row-perfect'][activeScore]);
    row.style.display = (text.includes(q) && sevOk && sOk) ? '' : 'none';
  });
}
function filterSev(btn, sev) {
  activeSev = sev;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterRows();
}
function filterScore(btn, score) {
  activeScore = (activeScore === score) ? null : score;
  btn.classList.toggle('active');
  filterRows();
}
"""

    # ── CSS (plain string) ──
    css = """
:root {
  --bg:#0f1117;--bg2:#1a1d26;--bg3:#22263a;--border:#2d3148;
  --text:#e0e4f0;--muted:#7a82a0;--green:#2ecc71;--red:#e74c3c;
  --orange:#e67e22;--blue:#3498db;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:var(--bg);color:var(--text);padding:24px;font-size:13px}
h1{font-size:22px;font-weight:700;margin-bottom:4px}
h2{font-size:15px;font-weight:600;color:var(--muted);margin:24px 0 12px}
.meta{color:var(--muted);font-size:12px;margin-bottom:24px}
.summary{display:flex;gap:16px;margin-bottom:28px;flex-wrap:wrap}
.stat{background:var(--bg2);border:1px solid var(--border);border-radius:10px;
      padding:16px 24px;text-align:center;min-width:100px}
.stat-value{font-size:28px;font-weight:700}
.stat-label{font-size:11px;color:var(--muted);margin-top:4px;text-transform:uppercase}
.cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:28px}
.cat-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.cat-header{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.cat-id{background:var(--bg3);border-radius:4px;padding:2px 6px;font-size:11px;font-weight:700;font-family:monospace}
.cat-name{flex:1;font-size:12px;font-weight:500}
.cat-score{font-weight:700;font-size:13px}
.cat-bar-bg{background:var(--bg3);border-radius:4px;height:6px}
.cat-bar{height:6px;border-radius:4px}
.cat-pct{font-size:11px;color:var(--muted);float:right;margin-top:4px}
.filters{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.filter-btn{background:var(--bg2);border:1px solid var(--border);border-radius:6px;
            padding:5px 12px;cursor:pointer;font-size:12px;color:var(--text)}
.filter-btn:hover,.filter-btn.active{background:var(--blue);border-color:var(--blue)}
input[type=search]{background:var(--bg2);border:1px solid var(--border);border-radius:6px;
                   padding:5px 12px;color:var(--text);font-size:12px;width:240px}
.results-table{width:100%;border-collapse:collapse}
.results-table th{background:var(--bg3);padding:8px 10px;text-align:left;
                  font-size:11px;color:var(--muted);text-transform:uppercase;
                  border-bottom:2px solid var(--border);white-space:nowrap}
.results-table td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
.results-table tr:hover{background:var(--bg2)}
.case-id{font-family:monospace;font-weight:700;font-size:12px}
.sev-badge{display:inline-block;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:700;color:#fff}
.score-badge{display:inline-block;border-radius:4px;padding:3px 8px;font-size:11px;font-weight:700;color:#fff;white-space:nowrap}
.lat-cell{white-space:nowrap;color:var(--muted);font-family:monospace;font-size:11px}
.files-cell{min-width:140px}
.file{font-size:10px;background:var(--bg3);padding:1px 5px;border-radius:3px;
      color:var(--blue);font-family:monospace;display:inline-block;margin:1px 0}
.response-preview{color:var(--muted);font-size:11px;line-height:1.5;margin-bottom:4px}
.reasoning{color:#a8b0cc;font-size:11px;font-style:italic;margin-top:4px}
.anti-pattern{color:var(--orange);font-size:11px;margin-top:4px}
.fix-hint{color:var(--blue);font-size:11px;margin-top:4px}
.flags{color:var(--red);font-size:10px;font-family:monospace;margin-top:4px}
.error-badge{background:var(--red);color:#fff;border-radius:4px;padding:2px 6px;font-size:10px}
.title-cell{min-width:160px;font-weight:500}
.response-cell{max-width:360px}
.critical-block{background:#2a1515;border:1px solid var(--red);border-radius:8px;
                padding:14px;margin-bottom:20px}
.critical-item{margin:4px 0;font-size:12px}
.file-table{width:100%;border-collapse:collapse;max-width:700px}
.file-table th{background:var(--bg3);padding:7px 10px;font-size:11px;
               color:var(--muted);text-transform:uppercase;border-bottom:2px solid var(--border)}
.file-table td{padding:7px 10px;border-bottom:1px solid var(--border)}
.dir-cell{color:var(--muted);font-size:11px;font-family:monospace}
.fail-count{background:var(--red);color:#fff;border-radius:12px;
            padding:1px 8px;font-size:11px;font-weight:700}
.table-wrap{overflow-x:auto}
"""

    return (
        '<!DOCTYPE html><html lang="pt-BR"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>LIA Eval Report — ' + run_date + '</title>'
        '<style>' + css + '</style>'
        '</head><body>'
        '<h1>LIA Eval Report</h1>'
        '<div class="meta">Generated ' + run_date + ' — Source: ' + esc(source_file) + '</div>'
        '<div class="summary">'
        '<div class="stat"><div class="stat-value" style="color:' + score_color + '">' + str(pass_pct) + '%</div><div class="stat-label">Pass Rate</div></div>'
        '<div class="stat"><div class="stat-value">' + str(passed) + '/' + str(total) + '</div><div class="stat-label">Cases Passed</div></div>'
        '<div class="stat"><div class="stat-value" style="color:var(--red)">' + str(len(critical_fails)) + '</div><div class="stat-label">Critical Fails</div></div>'
        '<div class="stat"><div class="stat-value">' + str(len(by_cat)) + '</div><div class="stat-label">Categories</div></div>'
        '</div>'
        + crit_block +
        '<h2>By Category</h2>'
        '<div class="cat-grid">' + cat_cards + '</div>'
        '<h2>All Results</h2>'
        '<div class="filters">'
        '<input type="search" id="search" placeholder="Search by ID, title, response…" oninput="filterRows()">'
        '<button class="filter-btn active" onclick="filterSev(this,\'all\')">All</button>'
        '<button class="filter-btn" onclick="filterSev(this,\'critical\')">Critical</button>'
        '<button class="filter-btn" onclick="filterSev(this,\'high\')">High</button>'
        '<button class="filter-btn" onclick="filterScore(this,0)">Fails only</button>'
        '</div>'
        '<div class="table-wrap">'
        '<table class="results-table" id="resultsTable">'
        '<thead><tr><th>ID</th><th>Sev</th><th>Title</th><th>Score</th><th>Latency</th><th>Files</th><th>Response / Analysis</th></tr></thead>'
        '<tbody>' + rows + '</tbody>'
        '</table></div>'
        '<h2>Files with Most Failures</h2>'
        '<table class="file-table">'
        '<thead><tr><th>File</th><th>Path</th><th>Fails</th></tr></thead>'
        '<tbody>' + file_rows + '</tbody>'
        '</table>'
        '<script>' + js + '</script>'
        '</body></html>'
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python eval_report.py <results_file.json>")
        sys.exit(1)
    results_path = Path(sys.argv[1])
    if not results_path.exists():
        print(f"File not found: {results_path}")
        sys.exit(1)
    results = json.loads(results_path.read_text())
    html = build_html(results, results_path.name)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = results_path.parent / f"eval_report_{ts}.html"
    out_path.write_text(html)
    print(f"\nHTML report: {out_path}")
    print(f"Open with:   open '{out_path}'\n")


if __name__ == "__main__":
    main()
