#!/usr/bin/env python3
"""
frontend-syntax-corruption — detecta corrupção de codemod em TS/TSX/JS/JSX.

Contexto: edições automatizadas (codemods/IA) já derrubaram o build do Next.js
várias vezes ao injetar código com sintaxe quebrada. Duas assinaturas recorrentes,
ambas causam "Parsing ecmascript source code failed" e tela branca no preview:

  1. Escape `\\n` LITERAL colado num statement (ex.: `\\nexport { X } from './x'`):
     a edição gravou a sequência de dois chars barra+n em vez de uma quebra de
     linha real, então o parser vê `\\nexport` e falha ("Expected unicode escape").

  2. `import`/`export ... from` com o módulo SEM ASPAS (ex.: `from ./ScheduleModal`):
     specifier de módulo não-string é sempre erro de sintaxe.

  3. Banner do proxy SSH do Replit ("Welcome to the Replit SSH Proxy.") gravado
     dentro do arquivo: quando a leitura via SSH falha, o conteúdo é sobrescrito
     pelo banner em texto puro, que não é código válido.

As três assinaturas NUNCA aparecem em código válido, então o sensor é seguro
(baixíssimo falso-positivo) e determinístico.

Uso:
  check_frontend_syntax_corruption.py            # escaneia arquivos STAGED (pre-commit)
  check_frontend_syntax_corruption.py <path>...  # escaneia path(s) recursivamente (make ci)

Exit 0 = limpo, Exit 1 = corrupção detectada. Output LLM-friendly (fix em PT-BR).
"""
import os
import re
import subprocess
import sys

EXTS = (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts")
SKIP_DIRS = {
    "node_modules", ".next", "dist", "build", ".turbo", "coverage",
    ".git", "__pycache__", ".cache", "out",
}

# Assinatura 1: escape `\n` literal colado a um keyword de statement.
# Em código-fonte saudável, "\nexport"/"\nimport"/"\nconst" como DOIS chars
# (barra + n) não existe fora de strings; a adjacência ao keyword torna
# o match específico da corrupção de codemod.
RE_LITERAL_NEWLINE_STMT = re.compile(
    r"\\n\s*(?:export|import|const|let|var|function|return|type|interface|enum)\b"
)

# Assinatura 2: linha import/export cujo `from` é seguido por specifier sem aspas.
# Casa `from ./x` / `from x` mas NÃO `from './x'` / `from "x"` / `from('x')`.
RE_UNQUOTED_FROM = re.compile(
    r"""^\s*(?:export|import)\b.*\bfrom\s+(?!['"(])\S"""
)

# Assinatura 3: banner do proxy SSH do Replit injetado no topo do arquivo.
# Quando uma ferramenta lê via SSH e a sessão falha, o conteúdo do arquivo é
# substituído/prefixado por este banner em texto puro, que NÃO é código válido
# e derruba o parser ("Welcome to the Replit SSH Proxy."). String fixa = zero
# falso-positivo. Verificada no texto BRUTO (não passa por _strip_literals).
RE_SSH_BANNER = re.compile(
    r"Welcome to the Replit SSH Proxy\.|docs\.replit\.com/replit-workspace/ssh"
)

# Strippers de literais — removem conteúdo de strings/templates/regex ANTES de
# casar as assinaturas, evitando falso-positivo quando `\n` aparece DENTRO de
# uma string (ex.: '```\nconst x') ou de uma regex (ex.: /...\nexport.../).
RE_STR_DQ = re.compile(r'"(?:[^"\\]|\\.)*"')
RE_STR_SQ = re.compile(r"'(?:[^'\\]|\\.)*'")
RE_STR_TPL = re.compile(r"`(?:[^`\\]|\\.)*`")
# Regex literal precedida por um contexto que NÃO permite divisão (logo é regex,
# não operador `/`). Cobre `.match(/.../)`, `= /.../`, `return /.../`, etc.
RE_REGEX_LIT = re.compile(
    r"([(,=:&|!?{;\[]|\breturn\b)(\s*)/(?:[^/\\\n]|\\.)+/[a-z]*"
)


def _strip_literals(line: str) -> str:
    line = RE_STR_TPL.sub('""', line)
    line = RE_STR_DQ.sub('""', line)
    line = RE_STR_SQ.sub('""', line)
    line = RE_REGEX_LIT.sub(r"\1\2", line)
    return line


def _workspace() -> str:
    return os.environ.get("WORKSPACE", "/home/runner/workspace")


def _staged_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, cwd=_workspace(), check=False,
        ).stdout
    except Exception:
        return []
    files = []
    for line in out.splitlines():
        line = line.strip()
        if line.endswith(EXTS):
            files.append(os.path.join(_workspace(), line))
    return files


def _walk(paths: list[str]) -> list[str]:
    files: list[str] = []
    for p in paths:
        if os.path.isfile(p) and p.endswith(EXTS):
            files.append(p)
            continue
        for root, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for n in names:
                if n.endswith(EXTS):
                    files.append(os.path.join(root, n))
    return files


def _scan_file(path: str) -> list[str]:
    issues: list[str] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return issues

    for i, raw in enumerate(lines, start=1):
        original = raw.rstrip("\n")
        if RE_SSH_BANNER.search(original):
            issues.append(
                f"{path}:{i}: banner do proxy SSH do Replit gravado dentro do arquivo "
                f"(leitura via SSH falhou e sobrescreveu o conteúdo)\n"
                f"    → {original.strip()[:120]}"
            )
        line = _strip_literals(original)
        if RE_LITERAL_NEWLINE_STMT.search(line):
            issues.append(
                f"{path}:{i}: escape `\\n` LITERAL colado a um statement "
                f"(codemod gravou barra+n em vez de quebra de linha real)\n"
                f"    → {original.strip()[:120]}"
            )
        if RE_UNQUOTED_FROM.search(line):
            issues.append(
                f"{path}:{i}: import/export com módulo SEM ASPAS\n"
                f"    → {original.strip()[:120]}"
            )
    return issues


def main(argv: list[str]) -> int:
    args = argv[1:]
    if args:
        files = _walk([os.path.abspath(a) for a in args])
        scope = "path(s): " + ", ".join(args)
    else:
        files = _staged_files()
        scope = "arquivos staged"

    all_issues: list[str] = []
    for f in files:
        all_issues.extend(_scan_file(f))

    if not all_issues:
        print(f"[frontend-syntax-corruption] OK ({len(files)} arquivo(s), {scope})")
        return 0

    print("[frontend-syntax-corruption] ❌ CORRUPÇÃO DE SINTAXE DETECTADA:", file=sys.stderr)
    for issue in all_issues:
        print(f"  {issue}", file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "[frontend-syntax-corruption] FIX:\n"
        "  • `\\n` literal: substitua a sequência barra+n por uma quebra de linha REAL\n"
        "    (cada statement na sua própria linha).\n"
        "  • from sem aspas: envolva o caminho do módulo em aspas, ex.:\n"
        "    export { X } from './X'   (não  from ./X)\n"
        "  • banner SSH: remova as linhas 'Welcome to the Replit SSH Proxy.' / link\n"
        "    docs.replit.com/.../ssh do topo do arquivo (restaure o conteúdo original).\n"
        "  Essas assinaturas quebram o build do Next.js (tela branca no preview).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
