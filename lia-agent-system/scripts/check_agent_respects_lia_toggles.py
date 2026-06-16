#!/usr/bin/env python3
"""
Anti-regression sensor (audit 2026-05-21, P0-1 follow-up): detect agent /
prompt-assembly modules that read canonical company fields (mission, vision,
values, tech_stack, ...) directly from ``CompanyProfile`` / ``CompanyCultureProfile``
WITHOUT first consulting ``lia_field_toggles`` via the canonical helper
``build_company_agent_context``.

## What this catches

A module that does any of:

    text = f"Mission: {profile.mission}"
    prompt += f"Values: {company.values}"
    if culture.evp_bullets: ...

is injecting authoritative-looking content into an LLM context bypassing
the recruiter's per-field opt-out. The 34 toggles + 34 instructions live
in ``CompanyCultureProfile.lia_field_toggles`` and ``.lia_instructions``;
ignoring them is the original ghost-setting bug.

## What it doesn't catch (yet)

- Indirect access via ``dict["mission"]``: harder regex, more false positives.
- CRUD endpoints that legitimately echo profile fields back to the recruiter
  (those are NOT LLM injection sites). Allowlisting handles those.
- Code that uses the helper correctly. We grep for the helper name's
  presence anywhere in the file as a coarse permit signal.

## Baseline-then-block ratchet

The sensor is INTENDED to start in warn-only mode and migrate to blocking
once the baseline is at 0. Current run: prints offenders with severity
WARN; CI integration as blocking step happens after the codebase clears
the queue.

## Allowlist

Files where direct profile-field access is intentional (read-only API
endpoints, repositories, migrations, scripts) live in
``ALLOWLIST_PREFIXES`` — additions require justification in the diff.
"""
from __future__ import annotations

import ast
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_ROOT = REPO_ROOT / "app/domains"

# Canonical 34 fields under lia_field_toggles control. Match
# ``LIA_FIELD_DEFINITIONS`` keys in
# ``plataforma-lia/src/hooks/company/use-company-lia-instructions.ts``.
CANONICAL_FIELDS = frozenset({
    "seniority_levels", "work_model", "hybrid_days_onsite", "employment_types",
    "salary_ranges", "trade_name", "industry", "website", "linkedin_url",
    "company_size", "employee_count", "founded_year", "mission", "vision",
    "values", "core_competencies", "engineering_culture", "default_languages",
    "company_big_five", "departments", "behavioral_competencies",
    "growth_opportunities", "dei_initiatives", "sustainability", "social_impact",
    "evp_bullets", "tech_stack", "benefits", "locations", "pipeline",
    "eligibility_questions", "headcount_planning", "leadership_style",
    "team_dynamics",
})

# Filenames whose role is to BUILD prompts / inject context. These are the
# canonical injection sites — they MUST respect toggles. Anything else
# (repositories, schemas, CRUD endpoints) can read freely.
TARGET_FILENAME_PATTERNS = (
    "context_aggregator",
    "_agent.py",
    "agents/",
    "_generator.py",
    "wsi_question_generator",
    "recruiter_assistant",
    "talent_pool",
    "jd_generator",
    "outreach",
)

# Allowlist: files known to be exempt (helpers themselves, repositories,
# legitimate non-LLM consumers). Paths relative to SCAN_ROOT.
#
# Adding a new entry requires:
#   1. Justification comment explaining why the file does NOT inject
#      profile fields directly into a system prompt.
#   2. Audit trace anchor (audit doc date) so the next reviewer knows
#      where the decision came from.
#   3. Ideally: an inline comment in the target file referencing this
#      allowlist + describing the upstream contract the caller must honor.
ALLOWLIST_PREFIXES = (
    # Repositories: they READ profile values without ever building prompts.
    "company/repositories/",
    "company_culture/repositories/",
    # The helper itself + its underlying service (target of compliance).
    "cv_screening/services/lia_field_config_service.py",
    # Context aggregator: it now consumes the helper (P0-1 integration).
    # Once migration is fully verified end-to-end this can stay allowlisted.
    "ai/services/context_aggregator_service.py",
    # Tool registry that returns STRUCTURED DATA back to the LLM via tool
    # call result, not via system-prompt injection. The LLM has already
    # received the filtered system prompt (via build_company_agent_context
    # upstream) before invoking the tool. This file reads fields from
    # DB query rows to populate the tool response dict — not a prompt
    # injection site. (Audit 2026-05-21, ratchet 2→0.)
    "hiring_policy/agents/policy_tool_registry.py",
    # Template builder for JD markdown. Accepts ``company_context`` as a
    # dict argument from the caller; the caller is responsible for filtering
    # via LiaFieldConfigService BEFORE invoking. The contract is documented
    # inline in the function docstring. (Audit 2026-05-21, ratchet 2→0.)
    "job_management/services/jd_generator_service.py",
)

# Magic string indicating the file has opted into the canonical helper.
HELPER_IMPORT_TOKEN = "build_company_agent_context"
HELPER_SVC_TOKEN = "LiaFieldConfigService"


def is_target_file(path: pathlib.Path) -> bool:
    s = str(path)
    return any(pat in s for pat in TARGET_FILENAME_PATTERNS)


def is_allowlisted(path: pathlib.Path) -> bool:
    rel = path.relative_to(SCAN_ROOT).as_posix()
    return any(rel.startswith(pref) for pref in ALLOWLIST_PREFIXES)


def file_uses_canonical_helper(text: str) -> bool:
    return HELPER_IMPORT_TOKEN in text or HELPER_SVC_TOKEN in text


# Exact name set — substring match (the prior approach) generates noise:
# ``pending_confirmations`` contains "co" and was matching as a profile-like
# binding. Names here must be the actual canonical bindings used in the
# codebase to mean "company profile / culture object".
_BINDING_NAMES_EXACT = frozenset({
    "profile", "company", "company_profile", "culture", "culture_profile",
    "culture_data", "company_data", "profile_data", "company_culture",
    "culture_row", "comp_data", "company_profile_data", "profile_row",
    "company_row", "comp_row", "company_context", "company_ctx",
})


def _name_hints_binding(node: ast.AST) -> bool:
    """Heuristic: does this AST node refer to a binding that looks like a
    profile/culture object?

    Strict exact-match against ``_BINDING_NAMES_EXACT`` — substring matching
    produced false positives on names like ``pending_confirmations`` (the "co"
    prefix matched). Better to miss one tenant-flavored alias than to fill
    the report with noise. If a new binding name shows up in the codebase,
    add it explicitly here.
    """
    if isinstance(node, ast.Name):
        return node.id in _BINDING_NAMES_EXACT
    if isinstance(node, ast.Attribute):
        return node.attr in _BINDING_NAMES_EXACT
    return False


def find_direct_field_reads(path: pathlib.Path) -> list[tuple[int, str, str]]:
    """Walk the AST for any of:

    1. ``<binding>.<canonical_field>`` — attribute access (original heuristic).
    2. ``<binding>["<canonical_field>"]`` / ``<binding>['<field>']`` — dict subscript.
    3. ``<binding>.get("<canonical_field>", ...)`` — dict get() with literal key.

    Where ``<binding>`` matches any of ``_BINDING_HINTS`` (looks like a
    profile/company/culture object).

    Returns a list of ``(line, field, access_kind)`` tuples — ``access_kind``
    is one of ``"attr"``, ``"subscript"``, ``"get"`` so the report tells the
    author what call shape needs to change.
    """
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return []
    hits: list[tuple[int, str, str]] = []
    # First pass: collect Attribute nodes that appear AS THE FUNCTION of a
    # Call (i.e. ``profile.values()`` — a method call, not a field read).
    # These must be excluded because Python's ``dict.values()`` collides with
    # our canonical ``values`` field name. Same logic protects ``profile.get(...)``
    # at the call-function position from being double-counted.
    called_attribute_ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            called_attribute_ids.add(id(node.func))

    for node in ast.walk(tree):
        # Pattern 1: profile.mission — Attribute access, NOT a method call.
        if isinstance(node, ast.Attribute):
            if id(node) in called_attribute_ids:
                continue  # it is a method call, e.g. dict.values()
            if (
                _name_hints_binding(node.value)
                and node.attr in CANONICAL_FIELDS
            ):
                hits.append((node.lineno, node.attr, "attr"))
                continue
        # Pattern 2: profile["mission"]
        if isinstance(node, ast.Subscript):
            slice_node = node.slice
            # Python 3.9+: Constant; earlier: Index(value=Constant). Guard both.
            const = (
                slice_node
                if isinstance(slice_node, ast.Constant)
                else getattr(slice_node, "value", None)
            )
            if (
                isinstance(const, ast.Constant)
                and isinstance(const.value, str)
                and const.value in CANONICAL_FIELDS
                and _name_hints_binding(node.value)
            ):
                hits.append((node.lineno, const.value, "subscript"))
                continue
        # Pattern 3: profile.get("mission", default)
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "get"
                and _name_hints_binding(func.value)
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value in CANONICAL_FIELDS
            ):
                hits.append((node.lineno, node.args[0].value, "get"))
                continue
    return hits


def main() -> int:
    if not SCAN_ROOT.exists():
        print(f"❌ Scan root not found: {SCAN_ROOT}", file=sys.stderr)
        return 2

    offenders: dict[pathlib.Path, list[tuple[int, str]]] = {}
    files_scanned = 0
    files_target = 0
    files_compliant = 0

    for path in sorted(SCAN_ROOT.rglob("*.py")):
        files_scanned += 1
        if not is_target_file(path):
            continue
        files_target += 1
        if is_allowlisted(path):
            continue
        text = path.read_text()
        if file_uses_canonical_helper(text):
            files_compliant += 1
            continue
        hits = find_direct_field_reads(path)
        if hits:
            offenders[path] = hits

    print(
        f"Scanned {files_scanned} .py files under {SCAN_ROOT.relative_to(REPO_ROOT)}, "
        f"of which {files_target} are LLM/prompt-target. {files_compliant} compliant."
    )
    if not offenders:
        print("✅ No agent/generator file reads canonical fields without the helper.")
        return 0

    print(
        f"\n⚠ {len(offenders)} agent/prompt-target file(s) read canonical "
        f"company fields directly without the lia_field_toggles helper.\n"
        f"Each call site below is a potential ghost-setting reintroduction "
        f"(toggle off in UI → field still injected into prompt).\n"
    )
    for path, hits in offenders.items():
        rel = path.relative_to(REPO_ROOT)
        print(f"  {rel}")
        for line, field, kind in hits[:10]:
            sample = {
                "attr": f"profile.{field}",
                "subscript": f'profile["{field}"]',
                "get": f'profile.get("{field}", ...)',
            }.get(kind, f"profile.{field}")
            print(f"    line {line}: {sample}")
        if len(hits) > 10:
            print(f"    ... +{len(hits) - 10} more")
        print()
    print(
        "Fix: replace direct reads with the canonical helper:\n"
        "    from app.shared.services.lia_agent_context_builder import "
        "build_company_agent_context\n"
        "    ctx_prompt = await build_company_agent_context(company_id, db)\n"
        "    # use ctx_prompt as the system-prompt fragment\n"
        "\n"
        "See CLAUDE.md section 'lia_field_toggles canonical pattern' for the "
        "full pattern and rationale.\n"
    )
    # Baseline-then-block: starts as WARN. Flip to ``return 1`` once the
    # offenders count reaches 0 (or matches an explicit baseline file).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
