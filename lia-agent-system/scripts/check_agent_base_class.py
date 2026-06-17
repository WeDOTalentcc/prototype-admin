#!/usr/bin/env python3
"""ADR-031 §4 / ADR-032 — sensores R1, R2, R3 para agentes.

R1: Agentes devem herdar de ComplianceDomainPrompt ou LangGraphReActBase
    (ou subclasse conhecida indireta).
R3: 'except Exception: pass' em agent files = silent fallback proibido
    (REGRA 4 CLAUDE.md). Honra marcador inline 'ADR-031-R3-EXEMPT: <reason>'.

Sensor computacional AST-based.
Exit 0 = sem violations. Exit 1 = violations (modo blocking).
Usage: python3 scripts/check_agent_base_class.py [--warn-only] [--rule R1,R3]
"""
import ast
import sys
from pathlib import Path

# Resolve raiz do projeto a partir do script
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DOMAINS_ROOT = PROJECT_ROOT / "app" / "domains"

# Classes base que garantem compliance (LGPD/fairness injeção no system prompt)
COMPLIANT_BASE_CLASSES = {
    # Base primárias
    "ComplianceDomainPrompt",
    "LangGraphReActBase",
    # Subclasses de LangGraphReActBase confirmadas no projeto:
    "SourcingReActAgent",        # sourcing/agents/sourcing_react_agent.py
    "KanbanReActAgent",          # recruiter_assistant/agents/kanban_react_agent.py
    "PipelineTransitionAgent",   # pipeline/agents/pipeline_transition_agent.py
    "CustomAgentRuntime",        # agent_studio/custom_agent_runtime.py
}

# Padrões de nome de arquivo de agente "real" (contém classes Agent)
# Exclui auxiliares: _tool_registry, _system_prompt, _stage_context, _tool_handler
AGENT_FILE_PATTERNS = {
    "*_react_agent.py",
    "*_agent.py",
    "agent.py",
    "*_runtime.py",
}

# Arquivos a ignorar explicitamente (não são agentes no sentido ADR-031)
IGNORE_FILES = {
    # Serviços com nome "agent" mas sem herança de agente
    "user_agent_preference_service.py",
    "autonomous_agent_service.py",
    "agent_quality_evaluator.py",
    # Grafos e nós LangGraph (não são agentes em si)
    "interview_graph.py",
    "interview_scheduling_nodes.py",
    "wsi_interview_graph.py",
    "pipeline_feedback_tool.py",
    # Arquivos de stage_context / system_prompt / tool_registry que ficam em agents/
    "stage_context.py",
    "system_prompt.py",
    "tool_registry.py",
}


def _is_agent_file(path: Path) -> bool:
    """Determina se o arquivo é um arquivo de agente real (não auxiliar)."""
    name = path.name
    if name.startswith("_") or name in IGNORE_FILES:
        return False
    if "_tool_registry" in name or "_system_prompt" in name or "_stage_context" in name:
        return False
    if "_tool_handler" in name or "_tools_extended" in name:
        return False
    # Deve ser um arquivo agent
    return any(path.match(p) for p in AGENT_FILE_PATTERNS) or "agent" in name


def check_r1_base_class(agent_file: Path) -> list[str]:
    """R1: agente herda de classe compliance-aware."""
    source = agent_file.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        name = node.name
        # Filtrar apenas classes que são agentes reais
        # Deve conter Agent, Runtime, Handler, Domain no nome
        is_agent_class = any(
            kw in name for kw in ["Agent", "Runtime", "Handler", "Domain"]
        )
        if not is_agent_class:
            continue
        # Pular classes de teste, mock, exceção, utilitárias
        skip_keywords = ["Test", "Mock", "Exception", "Error", "Repository",
                         "Service", "Mixin", "Base", "Enum", "State",
                         "Plugin", "Nodes", "Stage", "Block", "Record", "Graph"]
        if any(kw in name for kw in skip_keywords):
            continue
        if name.startswith("_"):
            continue

        base_names: set[str] = set()
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.add(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.add(base.attr)

        # Sem herança = classe standalone, não se aplica
        if not base_names:
            continue

        # "object" explícito = sem herança real
        effective_bases = base_names - {"object"}
        try:
            rel = agent_file.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = agent_file  # arquivo fora do projeto (ex: /tmp em testes)
        if not effective_bases:
            # herda só de object — não tem compliance
            violations.append(
                f"  [R1] {rel}:{node.lineno} — '{name}' sem herança de classe compliance-aware "
                f"(herda apenas de object).\n"
                f"  → Fix: herdar de LangGraphReActBase ou ComplianceDomainPrompt. "
                f"Se for subclasse indireta já compliant, adicionar a COMPLIANT_BASE_CLASSES no sensor."
            )
            continue

        compliant = effective_bases & COMPLIANT_BASE_CLASSES
        if not compliant:
            violations.append(
                f"  [R1] {rel}:{node.lineno} — '{name}' herda de {sorted(effective_bases)} "
                f"mas nenhuma é compliance-aware.\n"
                f"  → Fix: herdar de LangGraphReActBase ou ComplianceDomainPrompt. "
                f"Se for subclasse indireta já compliant, adicionar a COMPLIANT_BASE_CLASSES no sensor."
            )
    return violations


def check_r3_silent_fallback(agent_file: Path) -> list[str]:
    """R3: 'except Exception: pass' = silent fallback proibido em agentes.

    Honra marcador inline 'ADR-031-R3-EXEMPT' no bloco de comentário imediatamente
    dentro do except, ou 'R3-EXEMPT' como shorthand.
    """
    source = agent_file.read_text(encoding="utf-8")
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        # Apenas except genérico (sem type específico ou type=Exception)
        is_generic = (
            node.type is None
            or (isinstance(node.type, ast.Name) and node.type.id == "Exception")
        )
        if not is_generic:
            continue
        # Body deve ser SOMENTE 'pass' para ser silent fallback
        if not (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
            continue

        # Verificar marcador de isenção no source próximo à linha
        # Marcador: comentário com ADR-031-R3-EXEMPT ou R3-EXEMPT
        # Procura nas 3 linhas seguintes ao except (dentro do bloco)
        lineno = node.lineno - 1  # 0-indexed
        context_end = min(lineno + 5, len(lines))
        context = "\n".join(lines[lineno:context_end])
        if "ADR-031-R3-EXEMPT" in context or "R3-EXEMPT" in context:
            continue

        try:
            rel = agent_file.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = agent_file  # arquivo fora do projeto (ex: /tmp em testes)
        violations.append(
            f"  [R3] {rel}:{node.lineno} — 'except Exception: pass' "
            f"(silent fallback proibido — CLAUDE.md REGRA 4).\n"
            f"  → Fix: logger.error(exc_info=True) + raise, ou retornar com flag explícita. "
            f"  Para isenção justificada: adicionar comentário 'ADR-031-R3-EXEMPT: <motivo>'."
        )
    return violations


def find_agent_files() -> list[Path]:
    """Retorna lista de arquivos de agente reais nos domínios."""
    agent_files = []
    for domain_dir in sorted(DOMAINS_ROOT.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        agents_dir = domain_dir / "agents"
        if not agents_dir.is_dir():
            continue
        for py_file in sorted(agents_dir.glob("*.py")):
            if _is_agent_file(py_file):
                agent_files.append(py_file)
    return agent_files


def main() -> int:
    warn_only = "--warn-only" in sys.argv

    rule_filter: set[str] = set()
    for arg in sys.argv[1:]:
        if arg.startswith("--rule="):
            rule_filter = set(arg.split("=", 1)[1].split(","))

    agent_files = find_agent_files()

    violations_r1: list[str] = []
    violations_r3: list[str] = []

    for agent_file in agent_files:
        if not rule_filter or "R1" in rule_filter:
            violations_r1.extend(check_r1_base_class(agent_file))
        if not rule_filter or "R3" in rule_filter:
            violations_r3.extend(check_r3_silent_fallback(agent_file))

    all_violations = violations_r1 + violations_r3
    total = len(all_violations)

    if all_violations:
        print(f"ADR-031/032 agentes — {total} violation(s) encontrada(s):")
        if violations_r1:
            print(f"\nR1 — Base class compliance ({len(violations_r1)} violation(s)):")
            for v in violations_r1:
                print(v)
        if violations_r3:
            print(f"\nR3 — Silent fallback ({len(violations_r3)} violation(s)):")
            for v in violations_r3:
                print(v)
        if warn_only:
            print(f"\n[warn-only] {total} violation(s). Exit 0.")
            return 0
        return 1

    mode = "warn-only" if warn_only else "blocking"
    print(
        f"ADR-031/032 ✅ — {len(agent_files)} arquivo(s) de agente verificado(s), "
        f"0 violations (R1+R3, modo {mode})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
