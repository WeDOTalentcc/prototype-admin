"""Task #1166 — AST sentinel: forbid direct Anthropic construction inside
``app/domains/job_creation/``.

History (why this exists):
  - Task #1161 Bug A + Task #1164 Bug D both originated from wizard
    callsites instantiating ``langchain_anthropic.ChatAnthropic`` (or
    raw ``anthropic.Anthropic`` / ``AsyncAnthropic``) directly. The
    ``llm_bootstrap`` monkey-patch papered over the proxy-bypass, but
    the durability of that fix relies on every future caller going
    through one of those three SDK entry points.
  - This sentinel makes the contract explicit: inside the wizard
    domain (``app/domains/job_creation/``) Anthropic clients MUST be
    constructed via ``app.shared.providers.anthropic_client`` helpers
    (``get_chat_anthropic`` / ``get_anthropic_client`` /
    ``get_async_anthropic_client``). A baseline file lets us record
    pre-existing legacy callsites without exemption — the ratchet
    fails the build if a NEW direct construction appears, but legacy
    entries can be removed freely as we migrate them.

Forbidden constructor call names:
  - ``ChatAnthropic(...)``                 (LangChain wrapper)
  - ``AsyncAnthropic(...)``                (raw SDK async)
  - ``Anthropic(...)``                     (raw SDK sync)
  - ``anthropic.Anthropic(...)``           (raw SDK, dotted)
  - ``anthropic.AsyncAnthropic(...)``      (raw SDK async, dotted)
  - ``init_chat_model(provider="anthropic", ...)``
    and ``init_chat_model("anthropic:...", ...)``
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_ROOT = REPO_ROOT / "app" / "domains" / "job_creation"
HELPER_MODULE = REPO_ROOT / "app" / "shared" / "providers" / "anthropic_client.py"
BASELINE_FILE = REPO_ROOT / "tests" / ".baseline_anthropic_direct_construction_job_creation.txt"

FORBIDDEN_NAMES = frozenset({"ChatAnthropic", "AsyncAnthropic", "Anthropic"})

# Module names whose imports we treat as "Anthropic SDK access". Used to
# resolve aliases like ``import langchain_anthropic as lca`` →
# ``lca.ChatAnthropic(...)`` and ``from anthropic import Anthropic as A``
# → ``A(...)``.
ANTHROPIC_MODULES = frozenset({"anthropic", "langchain_anthropic"})


def _is_init_chat_model_anthropic(call: ast.Call) -> bool:
    """Match ``init_chat_model("anthropic:...")`` or
    ``init_chat_model(..., provider="anthropic")``."""
    func = call.func
    if isinstance(func, ast.Name) and func.id == "init_chat_model":
        pass
    elif isinstance(func, ast.Attribute) and func.attr == "init_chat_model":
        pass
    else:
        return False
    for kw in call.keywords:
        if kw.arg == "provider" and isinstance(kw.value, ast.Constant) and kw.value.value == "anthropic":
            return True
        if kw.arg == "model_provider" and isinstance(kw.value, ast.Constant) and kw.value.value == "anthropic":
            return True
    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
        if call.args[0].value.startswith("anthropic:") or call.args[0].value.startswith("anthropic/"):
            return True
    return False


def _collect_alias_maps(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Build per-file alias resolution.

    Returns:
        (name_aliases, module_aliases)
        - ``name_aliases``: local names that resolve to a forbidden
          Anthropic class. Covers
          ``from anthropic import Anthropic``,
          ``from anthropic import Anthropic as A``,
          ``from langchain_anthropic import ChatAnthropic as X``.
        - ``module_aliases``: local names that resolve to one of the
          Anthropic SDK modules. Covers
          ``import anthropic``,
          ``import anthropic as ant``,
          ``import langchain_anthropic as lca``,
          ``from langchain import anthropic`` (rare but possible).
    """
    name_aliases: set[str] = set()
    module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in ANTHROPIC_MODULES:
                    module_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod_root = (node.module or "").split(".")[0]
            if mod_root in ANTHROPIC_MODULES:
                for alias in node.names:
                    if alias.name in FORBIDDEN_NAMES:
                        name_aliases.add(alias.asname or alias.name)
    return name_aliases, module_aliases


def _is_forbidden_anthropic_call(
    call: ast.Call,
    *,
    name_aliases: set[str],
    module_aliases: set[str],
) -> bool:
    func = call.func

    # Bare-name call: covers
    #   ChatAnthropic(...) when imported as `from langchain_anthropic
    #   import ChatAnthropic` (or aliased to a different local name).
    if isinstance(func, ast.Name):
        if func.id in FORBIDDEN_NAMES or func.id in name_aliases:
            return True

    # Attribute call: covers any ``<module-or-alias>.ChatAnthropic(...)``
    # /``.AsyncAnthropic(...)``/``.Anthropic(...)``. We accept the call
    # when the attribute matches AND either (a) the root identifier is
    # a known Anthropic module / module-alias or (b) the attribute name
    # is uniquely Anthropic (``ChatAnthropic``/``AsyncAnthropic`` — no
    # other widely used class shares those names; restricting the
    # generic ``Anthropic`` attr keeps false positives like
    # ``self.Anthropic`` out).
    if isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_NAMES:
        root = func.value
        while isinstance(root, ast.Attribute):
            root = root.value
        if isinstance(root, ast.Name):
            if (
                root.id in ANTHROPIC_MODULES
                or root.id in module_aliases
                or func.attr in {"ChatAnthropic", "AsyncAnthropic"}
            ):
                return True

    if _is_init_chat_model_anthropic(call):
        return True
    return False


def _scan_file(path: Path) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    rel = path.relative_to(REPO_ROOT).as_posix()
    name_aliases, module_aliases = _collect_alias_maps(tree)
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_forbidden_anthropic_call(
            node, name_aliases=name_aliases, module_aliases=module_aliases,
        ):
            hits.append(f"{rel}:{node.lineno}")
    return hits


def _load_baseline() -> set[str]:
    if not BASELINE_FILE.exists():
        return set()
    out: set[str] = set()
    for line in BASELINE_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return out


def _collect_violations() -> set[str]:
    hits: set[str] = set()
    for py in DOMAIN_ROOT.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        hits.update(_scan_file(py))
    return hits


def test_helper_module_exposes_canonical_constructors():
    """The helper module exists and exports the three canonical seams."""
    assert HELPER_MODULE.exists(), (
        f"Expected canonical helper at {HELPER_MODULE.relative_to(REPO_ROOT)}"
    )
    source = HELPER_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for required in ("get_chat_anthropic", "get_anthropic_client", "get_async_anthropic_client"):
        assert required in defined, (
            f"anthropic_client.py must expose `{required}` (Task #1166)"
        )


def test_no_new_direct_anthropic_construction_in_job_creation():
    """Ratchet: no NEW direct ``ChatAnthropic``/``Anthropic``/``AsyncAnthropic``
    /``init_chat_model("anthropic:…")`` callsite may appear inside
    ``app/domains/job_creation/``. Existing legacy entries are tolerated via
    a baseline file and should be migrated over time.
    """
    violations = _collect_violations()
    baseline = _load_baseline()

    new_violations = sorted(violations - baseline)
    stale_baseline = sorted(baseline - violations)

    msg_parts: list[str] = []
    if new_violations:
        msg_parts.append(
            "New direct Anthropic construction detected in "
            "app/domains/job_creation/. Route through "
            "`app.shared.providers.anthropic_client.get_chat_anthropic()` "
            "(or the sync/async helpers) instead:\n  - "
            + "\n  - ".join(new_violations)
        )
    if stale_baseline:
        msg_parts.append(
            "Baseline contains entries that no longer exist — please "
            "remove them from "
            f"{BASELINE_FILE.relative_to(REPO_ROOT)} to keep the ratchet "
            "tight:\n  - " + "\n  - ".join(stale_baseline)
        )

    if msg_parts:
        pytest.fail("\n\n".join(msg_parts))


def test_canonical_callsites_use_helper():
    """The two callsites migrated by Task #1166 must import the helper."""
    expected = [
        REPO_ROOT / "app" / "domains" / "job_creation" / "services" / "intake_extractor.py",
        REPO_ROOT / "app" / "domains" / "job_creation" / "services" / "wizard_session_service.py",
    ]
    for path in expected:
        text = path.read_text(encoding="utf-8")
        assert "from app.shared.providers.anthropic_client import" in text, (
            f"{path.relative_to(REPO_ROOT)} must import the centralized "
            "Anthropic helper (Task #1166)."
        )
