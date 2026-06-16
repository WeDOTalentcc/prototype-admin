"""UC-P1-17/18/19: Domain coupling regression tests.

UC-P1-17: sourcing MUST NOT import credits domain.
UC-P1-18: sourcing MUST NOT use top-level (module-scope) RAG imports.
          Known lazy coupling: sourcing_tool_registry.py line 1340 uses a
          lazy import inside a function body — acceptable for now, tracked
          as technical debt. This test prevents it from becoming top-level.
UC-P1-19: job_management ↔ recruiter_assistant MUST NOT have top-level
          (module-scope) circular imports. Known lazy cross-domain calls
          exist in wizard_action_executor.py / job_vacancy_service.py /
          jd_template_service.py — all lazy-imported inside function bodies
          to avoid import-time circular deps. This test prevents promotion
          to top-level imports.
"""
import subprocess


_BASE = "/home/runner/workspace/lia-agent-system"


def _grep(pattern: str, path: str) -> list[str]:
    """Return non-pycache lines matching pattern under path."""
    result = subprocess.run(
        ["grep", "-r", "--include=*.py", "-E", "--with-filename", "-n",
         pattern, path],
        capture_output=True,
        text=True,
        cwd=_BASE,
    )
    return [l for l in result.stdout.splitlines() if "__pycache__" not in l]


def _top_level_only(lines: list[str]) -> list[str]:
    """Filter to lines that are top-level imports (not indented inside a function/class)."""
    # Top-level lines: the content after "filename:linenum:" starts with from or import
    top = []
    for line in lines:
        # Format: "path/file.py:42:    from foo import bar"
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        code = parts[2]
        # If the code part starts with from or import (no leading whitespace) → top-level
        if code.lstrip() and not code[0].isspace():
            top.append(line)
    return top


# ---------------------------------------------------------------------------
# UC-P1-17: sourcing → credits
# ---------------------------------------------------------------------------

def test_sourcing_does_not_import_credits():
    """sourcing domain must not import credits domain or call credit functions."""
    hits = _grep(
        r"from[[:space:]].*credits|import[[:space:]].*credits|deduct_credit|consume_credit",
        "app/domains/sourcing/",
    )
    assert not hits, (
        "UC-P1-17 VIOLATION — sourcing→credits coupling found:\n" + "\n".join(hits)
    )


# ---------------------------------------------------------------------------
# UC-P1-18: sourcing → RAG (top-level only)
# ---------------------------------------------------------------------------

def test_sourcing_does_not_have_toplevel_rag_import():
    """sourcing must not import RAG pipeline at module (top) level.

    Lazy imports inside function bodies are tolerated as technical debt but
    must not escalate to module-scope. This test prevents that escalation.
    """
    all_hits = _grep(
        r"from app\.shared\.rag|from app\.domains\.ai\.services\.rag_pipeline_service"
        r"|import rag_pipeline_service",
        "app/domains/sourcing/",
    )
    top_level = _top_level_only(all_hits)
    assert not top_level, (
        "UC-P1-18 VIOLATION — top-level sourcing→RAG import found "
        "(lazy imports inside functions are tolerated, top-level are not):\n"
        + "\n".join(top_level)
    )


# ---------------------------------------------------------------------------
# UC-P1-19: circular dependency job_management ↔ recruiter_assistant
# ---------------------------------------------------------------------------

def test_no_toplevel_job_management_to_recruiter_assistant():
    """job_management must not have top-level imports of recruiter_assistant.

    Lazy imports inside functions are an existing technical debt (wizard
    services). Top-level imports would make the circular dep un-breakable.
    """
    all_hits = _grep(
        r"from[[:space:]].*recruiter_assistant|import[[:space:]].*recruiter_assistant",
        "app/domains/job_management/",
    )
    top_level = _top_level_only(all_hits)
    assert not top_level, (
        "UC-P1-19 VIOLATION — top-level job_management→recruiter_assistant import:\n"
        + "\n".join(top_level)
    )


def test_no_toplevel_recruiter_assistant_to_job_management():
    """recruiter_assistant must not have top-level imports of job_management.

    Same technical debt caveat as above. This test prevents promotion
    of lazy-imports to module-scope.
    """
    all_hits = _grep(
        r"from[[:space:]].*job_management|import[[:space:]].*job_management",
        "app/domains/recruiter_assistant/",
    )
    top_level = _top_level_only(all_hits)
    assert not top_level, (
        "UC-P1-19 VIOLATION — top-level recruiter_assistant→job_management import:\n"
        + "\n".join(top_level)
    )
