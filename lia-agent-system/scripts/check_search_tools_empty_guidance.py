#!/usr/bin/env python3
"""Sensor canonical (2026-06-04): search/list tools em 0-resultados DEVEM emitir
sinal estruturado de relaxamento (build_empty_result_guidance), nunca lista vazia
silenciosa. Extensao da REGRA 4 (anti-fallback-silencioso) + Fase B P0.2 (autocorrecao).

Heuristica conservadora (evitar falso-positivo, licao harness "medir o sensor"):
funcao cujo NOME contem search/find (busca filtrada relaxavel) E que RETORNA dict\ncom chave "total" E uma chave-lista
("candidates"|"jobs"|"results"|"items"|"pools"|"talent_pools") e produtora de
resultado de busca. Se o corpo NAO referencia build_empty_result_guidance (direto ou
via _format_*_result) e nao tem marker # GUIDANCE-EXEMPT -> violacao.

Escopo: app/domains/**/tools/**/*.py + app/domains/**/agents/*tool*registry*.py.
warn-only default; --blocking exit 1 se total > --max (default 0).
Output otimizado p/ LLM (instrucao de fix embutida).
"""
from __future__ import annotations
import ast, sys, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERNS = ["app/domains/**/tools/**/*.py", "app/domains/**/agents/*tool*registry*.py"]
LIST_KEYS = {"candidates", "jobs", "results", "items", "pools", "talent_pools"}
SAFE = ("build_empty_result_guidance", "_format_search")
EXEMPT = "GUIDANCE-EXEMPT"


def _dict_str_keys(node):
    keys = set()
    if isinstance(node, ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                keys.add(k.value)
    return keys


def scan_file(path):
    rel = os.path.relpath(path, ROOT)
    try:
        text = open(path, encoding="utf-8").read()
    except Exception:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.splitlines()
    viol = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body_src = "\n".join(lines[node.lineno - 1: node.end_lineno])
        if EXEMPT in body_src or any(s in body_src for s in SAFE):
            continue
        is_search_result = False
        for n in ast.walk(node):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
                allkeys = set(_dict_str_keys(n.value))
                for v in n.value.values:
                    allkeys |= _dict_str_keys(v)
                if "total" in allkeys and (allkeys & LIST_KEYS):
                    is_search_result = True
                    break
        name_l = node.name.lower()
        looks_like_search = ("search" in name_l) or ("find" in name_l)
        if is_search_result and looks_like_search:
            viol.append((rel, node.lineno, node.name))
    return viol


def main():
    blocking = "--blocking" in sys.argv
    maxv = 0
    for a in sys.argv:
        if a.startswith("--max="):
            maxv = int(a.split("=", 1)[1])
    files = set()
    for p in PATTERNS:
        files.update(glob.glob(os.path.join(ROOT, p), recursive=True))
    allv = []
    for f in sorted(files):
        allv.extend(scan_file(f))
    for rel, ln, fn in allv:
        print(f"[GUIDANCE] {rel}:{ln} {fn}() retorna resultado de busca SEM build_empty_result_guidance")
    if allv:
        print(f"\n{len(allv)} search tool(s) sem guidance de 0-resultados.")
        print("Fix: formate via _format_<entity>_result usando build_empty_result_guidance")
        print("(app/orchestrator/context/empty_result_guidance.py). Em 0-resultados retorne")
        print("sinal estruturado {empty, relaxation_suggestions, applied_filters}, nunca lista")
        print("vazia silenciosa (REGRA 4 anti-fallback). Opt-out: # GUIDANCE-EXEMPT: <motivo>.")
    else:
        print("OK — search tools com guidance de 0-resultados.")
    return 1 if (blocking and len(allv) > maxv) else 0


if __name__ == "__main__":
    sys.exit(main())
