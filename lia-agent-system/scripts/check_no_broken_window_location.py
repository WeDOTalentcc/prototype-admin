#!/usr/bin/env python3
"""
check_no_broken_window_location.py — sensor anti-regressão Task #712.

Onda 4 (2026-05-24): protege contra reincidência do bug onde código TS
faz `window.location.href = "/X"` mas a rota `/X` (page.tsx) não existe
em src/app/**.

Histórico: Task #712 (commit d1ed07e4d0 2026-04-20) introduziu
`window.location.href = "/onboarding"` em onboarding-controller.tsx mas
NUNCA criou src/app/[locale]/onboarding/page.tsx. Resultado: usuário
novo que clicou "Start Setup Wizard" caiu em 404 por 35 dias.

Fix da rota: commit 09ea1203c (Onda 4-N1-revised).
Sensor pra prevenir reincidência: este arquivo.

Heurística:
1. Scanea TS/TSX por padrão `window.location.href = "/X"` ou
   `window.location.assign("/X")` ou `router.push("/X")` ou
   `router.replace("/X")` com path STÁTICO.
2. Path dinâmico (template literal, var) é SKIPPED — fora do escopo
   (esses sites costumam ter target variável).
3. Allowlist: paths conhecidos sem page.tsx em src/app/** mas validos
   por outro motivo (e.g. /api/* endpoints, externos, fragmentos #).
4. Para cada path estático coletado, verifica se existe correspondente
   src/app/[locale]/{path}/page.tsx OU src/app/{path}/page.tsx OU
   src/app/[locale]/(dashboard)/{path}/page.tsx.

Output otimizado para consumo de LLM (REGRA harness).

Exit codes:
- 0: zero violations
- 1: ≥1 violation (BLOCKING quando wired em CI)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # /home/runner/workspace
FRONT = REPO / "plataforma-lia"
SRC = FRONT / "src"
APP = SRC / "app"

# Paths excluded from validation (legítimos sem page.tsx local)
ALLOWLIST = {
    # APIs (handled by route.ts not page.tsx)
    "/api",
    # External or fragment links
    "/",
    # Auth/login redirects (validado em layouts existentes)
    "/login",
    # Logout endpoint
    "/logout",
}

# Pattern: capture path string em window.location.X / router.push/replace
# Match: 'X' "X" `X` (apenas STATIC string literals, no interpolation)
NAV_PATTERNS = [
    re.compile(r'window\.location\.href\s*=\s*["\']([^"\'`${}]+)["\']'),
    re.compile(r'window\.location\.assign\s*\(\s*["\']([^"\'`${}]+)["\']\s*\)'),
    re.compile(r'window\.location\.replace\s*\(\s*["\']([^"\'`${}]+)["\']\s*\)'),
    re.compile(r'\brouter\.(?:push|replace)\s*\(\s*["\']([^"\'`${}]+)["\']\s*\)'),
]


def normalize_path(p: str) -> str:
    """Strip query/fragment, trailing slash; keep leading /."""
    p = p.split("?")[0].split("#")[0]
    if p != "/" and p.endswith("/"):
        p = p[:-1]
    return p


def path_exists_in_app(p: str) -> bool:
    """Check if path resolves to a page.tsx under src/app/**."""
    if not p.startswith("/"):
        return True  # not a route (anchor, relative)
    if p in ALLOWLIST:
        return True
    if any(p.startswith(prefix) for prefix in ALLOWLIST if prefix != "/"):
        return True

    p_clean = p.lstrip("/")
    # Try these candidates:
    candidates = [
        APP / p_clean / "page.tsx",
        APP / "[locale]" / p_clean / "page.tsx",
        APP / "[locale]" / "(dashboard)" / p_clean / "page.tsx",
    ]
    return any(c.exists() for c in candidates)


def scan_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, full_match, extracted_path) for each broken nav."""
    findings: list[tuple[int, str, str]] = []
    try:
        text = filepath.read_text()
    except (UnicodeDecodeError, PermissionError):
        return findings

    for i, line in enumerate(text.split("\n"), start=1):
        # Skip comments
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        for pattern in NAV_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            path = normalize_path(match.group(1))
            if not path_exists_in_app(path):
                findings.append((i, line.strip(), path))
                break  # one finding per line
    return findings


def main() -> int:
    if not SRC.exists():
        print(f"❌ Diretório não encontrado: {SRC}", file=sys.stderr)
        return 1

    all_findings: list[tuple[Path, int, str, str]] = []
    scanned = 0

    for filepath in SRC.rglob("*.ts*"):
        if filepath.suffix not in (".ts", ".tsx"):
            continue
        # Skip generated, .d.ts, tests, node_modules
        skip_parts = {"node_modules", ".next", "__tests__", "__generated__", ".generated"}
        if any(part in skip_parts for part in filepath.parts):
            continue
        if filepath.name.endswith(".d.ts"):
            continue
        if filepath.name.endswith(".test.ts") or filepath.name.endswith(".test.tsx"):
            continue
        if filepath.name.endswith(".spec.ts") or filepath.name.endswith(".spec.tsx"):
            continue
        scanned += 1

        findings = scan_file(filepath)
        for line_no, full_match, path in findings:
            all_findings.append((filepath.relative_to(REPO), line_no, full_match, path))

    if all_findings:
        print(f"❌ {len(all_findings)} site(s) com window.location/router.push pra rota INEXISTENTE:")
        print()
        for rel_path, line_no, full_match, target in all_findings:
            print(f"  {rel_path}:{line_no}")
            print(f"    Target: {target!r}  → NÃO existe page.tsx correspondente")
            print(f"    Linha: {full_match[:100]}")
            print(f"    Fix:")
            print(f"      a) Criar plataforma-lia/src/app/[locale]{target}/page.tsx")
            print(f"      b) OU plataforma-lia/src/app/[locale]/(dashboard){target}/page.tsx")
            print(f"      c) OU corrigir o target pra rota válida existente")
            print(f"      d) OU adicionar {target!r} ao ALLOWLIST deste sensor se legítimo")
            print()
        print(f"Total scanned: {scanned} TS/TSX files")
        print(f"Ref: Task #712 (commit d1ed07e4d0) — bug que motivou este sensor")
        return 1

    print(f"✅ {scanned} TS/TSX files OK (zero window.location/router.push pra rota inexistente)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
