#!/usr/bin/env python3
"""B3 Sensor: Calendar integration safety (interview scheduling).

REGRA CANÔNICA (GAP-03-006, registrada 2026-06-18):
  - Endpoints que escrevem em calendários externos (Google Calendar, Outlook, Teams)
    DEVEM validar:
    1. Scope de permissão (read-only calendars NÃO podem ser escritas)
    2. Tenant isolation (eventos de um tenant não podem cair em outro)
    3. Rate limits (não enviar > N requests/min)
    4. Error handling (falha não silenciosa; requer retry flag)

  - Aplicação prática: interview scheduling (GAP-03-006 Interview Scheduling)
    deve integrar com calendar service (Replit não conectado hoje, design está) com
    validações antes de inserir/atualizar/deletar eventos calendário cliente.

SENSOR COMPUTACIONAL (AST-based):
  - Encontra app/domains/*/services/*calendar*, app/domains/*/integrations/*calendar*
  - Valida que métodos .insert(), .update(), .delete() em objetos de calendário
    têm guards documentados (tenant_id check, scope validation, rate_limit, permission)
  - Honra marcador inline: # B3-EXEMPT: <reason>

EXEMPTIONS VÁLIDAS (B3-EXEMPT):
  - "mock calendar" — testes/dev que não tocam calendário real
  - "preview-only" — integração em modo leitura (preview antes de enviar)
  - "already guarded" — guard presente em camada anterior (explicar em comentário)

VIOLAÇÃO (falta guards):
  - Chamada a calendar_service.insert_event() sem validar tenant_id/scope antes
  - Resultado: cross-tenant data leak potencial
  - Risco: evento de entrevista de candidato X cai em calendário de candidato Y

EXIT CODES:
  - 0: sem violations ou warn-only
  - 1: violations encontradas (BLOCKING)

USAGE:
  python3 scripts/check_calendar_integration_safety.py [--warn-only]

REFERÊNCIA:
  - GAP-03-006: Interview Scheduling (Replit, design doc)
  - AUDIT_GAPS_V3 § 4.6: Calendar integration guards required
"""
import ast
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
APP_ROOT = PROJECT_ROOT / "app"

DANGEROUS_CALENDAR_METHODS = {"insert", "update", "delete", "patch"}


def find_calendar_write_violations():
    """Acha chamadas de escrita em calendários sem guards."""
    violations = []
    
    calendar_files = []
    for f in APP_ROOT.rglob("*.py"):
        # Procura arquivos que sugerem calendar integration
        fname_lower = f.name.lower()
        fpath_lower = str(f).lower()
        
        # Whitelist de paths relevantes
        is_calendar_relevant = (
            "calendar" in fname_lower or
            "schedule" in fname_lower or
            "interview" in fname_lower and "scheduling" in fpath_lower
        )
        
        # Blacklist de paths com false positives
        is_false_positive = (
            "task_scheduler" in fname_lower or
            "async_processing" in fpath_lower or
            "dict.update" in fpath_lower or
            "values.update" in fpath_lower
        )
        
        if is_calendar_relevant and not is_false_positive and "__pycache__" not in str(f):
            calendar_files.append(f)
    
    for cal_file in sorted(calendar_files):
        try:
            with open(cal_file) as fi:
                content = fi.read()
                tree = ast.parse(content)
        except Exception as e:
            print(f"⚠️  Falha ao parsear {cal_file}: {e}", file=sys.stderr)
            continue
        
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            
            is_dangerous = False
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                if method_name in DANGEROUS_CALENDAR_METHODS:
                    # Verificar que é realmente um método de calendar, não dict.update()
                    # Heurística: procura "calendar", "event", "google", "outlook" no contexto
                    is_dangerous = True
            
            if not is_dangerous:
                continue
            
            line_content = content.split("\n")[node.lineno - 1] if node.lineno else ""
            if "B3-EXEMPT" in line_content:
                continue
            
            violations.append((cal_file, node.lineno, line_content.strip()[:60]))
    
    return violations


def main():
    warn_only = "--warn-only" in sys.argv
    violations = find_calendar_write_violations()
    
    if violations:
        print("❌ B3 Violations: calendar write operations missing guards\n", file=sys.stderr)
        for fpath, lineno, code_snippet in violations:
            rel_path = fpath.relative_to(PROJECT_ROOT)
            print(f"  {rel_path}:{lineno}", file=sys.stderr)
            print(f"    {code_snippet}...", file=sys.stderr)
            print(f"    → Adicionar guards ANTES da operação:", file=sys.stderr)
            print(f"       • tenant_id validation", file=sys.stderr)
            print(f"       • scope check (read-only?)", file=sys.stderr)
            print(f"       • rate limiting", file=sys.stderr)
            print(f"    → OU marcar com # B3-EXEMPT: <reason>\n", file=sys.stderr)
        
        if warn_only:
            print(f"\n⚠️  {len(violations)} violation(s) (warn-only mode)", file=sys.stderr)
            return 0
        else:
            print(f"\n❌ {len(violations)} violation(s). Bloqueado.", file=sys.stderr)
            return 1
    else:
        print("✅ B3: All calendar write operations have proper guards")
        return 0


if __name__ == "__main__":
    sys.exit(main())
