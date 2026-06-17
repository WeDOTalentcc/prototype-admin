#!/usr/bin/env python3
"""
check_slash_command_contract.py — AST-ish sensor canonical para slash-commands.ts

Onda 4-N4 (2026-05-24): sensor pedido pelo audit unified_chat_audit.md
(linha 481) mas nunca criado. P1-2 (commit 69bb4b8ab) corrigiu /feedback e
/agendar manualmente mas não previne reincidência.

Contrato canonical:
- Todo SLASH_COMMAND em slash-commands.ts DEVE ter ao menos UM de:
    1. buildBareMessage função (handler local pra bare command)
    2. dropdownPrefill string não-vazia (pré-preenche input)
    3. id em EXECUTE_ONLY_COMMAND_IDS (intercept local, executa direto)

Quem viola: command vai pro LLM como string crua (ex: "/feedback") sem
contexto, LLM responde "Não entendi" → broken UX.

Output otimizado para consumo de LLM (REGRA harness):
- file:line + cmd_id + reason + fix sugerido

Exit codes:
- 0: zero violations
- 1: ≥1 violation (BLOCKING quando wired em CI)
"""
import re
import sys
from pathlib import Path

SLASH_FILE = Path("plataforma-lia/src/components/unified-chat/slash-commands.ts")

# Commands que executam direto sem precisar de bare/prefill (intercept local em useSlashCommands)
EXECUTE_ONLY_COMMAND_IDS = {
    "ajuda",          # renderiza help card via intercept local
    "nova-conversa",  # reseta state via onExecuteCommand
    "definir",        # bare = abre input pra usuário digitar TERM
}


def main() -> int:
    if not SLASH_FILE.exists():
        print(f"❌ Arquivo não encontrado: {SLASH_FILE}", file=sys.stderr)
        return 1

    text = SLASH_FILE.read_text()

    # Match entries `{ id: "..." ... }` em SLASH_COMMANDS array
    # Pattern: cada entry começa com `{` em nova linha, contém `id: "..."`, termina antes do próximo `{` ou fim do array
    entries = re.findall(
        r'\{\s*id:\s*"([^"]+)"(.*?)\}\s*,',
        text,
        re.DOTALL,
    )

    failures: list[tuple[str, str]] = []

    for cmd_id, body in entries:
        if cmd_id in EXECUTE_ONLY_COMMAND_IDS:
            continue

        has_bare = bool(re.search(r'\bbuildBareMessage\s*[:=]', body))
        has_prefill = bool(re.search(r'\bdropdownPrefill\s*:\s*"[^"]+"', body))

        if not (has_bare or has_prefill):
            failures.append((cmd_id, "missing buildBareMessage AND dropdownPrefill"))

    if failures:
        print(f"❌ {len(failures)} slash command(s) violam contrato canonical:")
        print()
        for cmd_id, reason in failures:
            print(f"  - id={cmd_id!r}")
            print(f"    Reason: {reason}")
            print(f"    Fix: adicionar UM de:")
            print(f"      a) buildBareMessage: () => 'mensagem default pro LLM'")
            print(f"      b) dropdownPrefill: '/{cmd_id} '  (pré-preenche input)")
            print(f"      c) adicionar '{cmd_id}' em EXECUTE_ONLY_COMMAND_IDS deste sensor")
            print()
        print(f"Arquivo: {SLASH_FILE}")
        print(f"Ref: audit unified_chat_audit.md P1-2 (commit 69bb4b8ab)")
        print(f"Doc: ~/Documents/wedotalent_audit_2026-05-24/CANONICAL_FIX_PLAN_UNIFIED_CHAT.md (N4)")
        return 1

    print(f"✅ {len(entries)} slash commands OK (contrato canonical respeitado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
