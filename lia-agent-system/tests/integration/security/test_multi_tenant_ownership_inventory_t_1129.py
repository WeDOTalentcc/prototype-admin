"""T-1129 sealing — Sentinela de inventário canônico multi-tenant ownership.

Esta suíte é o **gate AST** que protege contra regressão dos contratos de
ownership entregues pelas tasks #1129a..f:

    (a) `test_no_endpoint_missing_require_company_id_gate` — todo
        `@router.{get,post,...}` em `app/api/v1/**` declara
        `Depends(_require_company_id)` (ou o router inteiro carrega o
        gate via `APIRouter(dependencies=[...])`). Exceções legítimas
        ficam em `tests/.allowlist_public_endpoints.txt`; débito legado
        é tolerado via baseline ratchet em
        `tests/.baseline_endpoint_no_gate.txt`.
    (b) `test_no_redis_key_without_tenant_namespace` — chamadas em
        clientes Redis (`redis`, `aioredis`, `redis.asyncio`) **import-
        aware**: só arquivos que importam um desses módulos são
        analisados, e só receivers em uma whitelist estrita
        (`redis`, `r`, `_redis`, `redis_client`, `cache`, `cache_client`).
        Chave deve usar `tenant_namespaced_key(...)` ou conter
        `{company_id}`/`{tenant_id}` no literal f-string.
    (c) `test_no_es_search_without_tenant_filter` — chamadas
        `<es>.search/count/msearch` **import-aware** (arquivo precisa
        importar `elasticsearch`/`opensearchpy`) devem envelopar a query
        em `with_tenant_filter(...)` ou usar `TenantAwareEsClient`.
    (d) `test_no_celery_task_without_tenant_aware_base` — todo decorator
        `@celery_app.task` / `@shared_task` em `app/jobs/tasks/**`
        declara `base=TenantAwareTask`.
    (e) `test_no_legacy_cross_tenant_session_usage` — símbolo
        `cross_tenant_session_legacy` não aparece em nenhum import /
        attribute / chamada do `app/` (visita AST, não grep).

Padrão segue `tests/integration/agents/test_tenant_aware_rollout_t_d.py`.

## Ratchet baseline

`_assert_no_new_violations(...)` compara o set atual com o snapshot do
arquivo `.baseline_*.txt` (uma `relpath:lineno` por linha). O build
quebra apenas em violações novas; melhorar a baseline (remover linhas)
é encorajado e validado por um teste meta. Esse é o mesmo pattern usado
por ruff/mypy em monorepos com débito histórico, e permite que o gate
seja **strict-block** desde o primeiro dia sem precisar refatorar 295
endpoints + 88 tabelas legacy num só PR.

## Hardening pós-review (code_review REJECTED v1 + v2)

* (b) e (c) agora são **import-aware**: receiver name DEVE estar na
  whitelist E o arquivo DEVE importar o cliente Redis/ES. Removidos os
  bypasses heurísticos `"key" in name` e `client` genérico.
* (a) e (c) e (b) ganharam ratchet baseline (regressão = quebra build,
  débito legado = tracked).
* (e) migrou de regex para visita AST cobrindo `Name`, `Attribute`,
  `ImportFrom`/`as`.

Origem: Task #1149 (T-1129 sealing).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = REPO_ROOT / "app"
API_V1_DIR = APP_DIR / "api" / "v1"
JOBS_TASKS_DIR = APP_DIR / "jobs" / "tasks"
ALLOWLIST_FILE = REPO_ROOT / "tests" / ".allowlist_public_endpoints.txt"
BASELINE_ENDPOINT_FILE = REPO_ROOT / "tests" / ".baseline_endpoint_no_gate.txt"
BASELINE_REDIS_FILE = REPO_ROOT / "tests" / ".baseline_redis_no_namespace.txt"
BASELINE_ES_FILE = REPO_ROOT / "tests" / ".baseline_es_no_tenant_filter.txt"

ROUTER_METHOD_DECORATORS = {"get", "post", "put", "patch", "delete"}
GATE_FUNCTION_NAMES = {"_require_company_id", "require_company_id"}


# =============================================================================
# Shared helpers
# =============================================================================


def _load_lines(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


def _iter_python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*.py") if "__pycache__" not in p.parts
    )


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return None


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _violation_key(rel: str, lineno: int) -> str:
    return f"{rel}:{lineno}"


def _assert_no_new_violations(
    *,
    current: set[str],
    baseline: set[str],
    label: str,
    remediation: str,
) -> None:
    new = sorted(current - baseline)
    fixed = sorted(baseline - current)
    msg_parts: list[str] = []
    if new:
        msg_parts.append(
            f"T-1129 sealing — {len(new)} new {label} violation(s):\n  "
            + "\n  ".join(new[:50])
            + (f"\n  ... (+{len(new) - 50} more)" if len(new) > 50 else "")
            + f"\n{remediation}"
        )
    assert not msg_parts, "\n\n".join(msg_parts)
    # Soft signal — baseline got better. Print so CI surfaces the win,
    # but don't fail (otherwise contributors would need to update the
    # baseline file in the same PR that fixes the debt, which is fine
    # but better handled by the dedicated baseline-drift test below).
    if fixed:
        print(
            f"[T-1129 ratchet] {label}: baseline shrank by {len(fixed)}. "
            "Update the baseline file in this PR to lock in the gain."
        )


def _assert_baseline_in_sync(
    *,
    current: set[str],
    baseline: set[str],
    baseline_file: Path,
    label: str,
) -> None:
    """Fails if baseline lists violations that no longer exist (stale)."""
    stale = sorted(baseline - current)
    assert not stale, (
        f"T-1129 ratchet — baseline `{baseline_file.name}` is stale: "
        f"{len(stale)} {label} entries no longer match current code. "
        "Remove them from the baseline file to lock in the improvement.\n  "
        + "\n  ".join(stale[:30])
    )


# =============================================================================
# (a) Endpoint gate inventory
# =============================================================================


def _apirouter_call_has_gate(call: ast.Call) -> bool:
    for kw in call.keywords or []:
        if kw.arg != "dependencies" or not isinstance(
            kw.value, (ast.List, ast.Tuple)
        ):
            continue
        for elt in kw.value.elts:
            if (
                isinstance(elt, ast.Call)
                and isinstance(elt.func, ast.Name)
                and elt.func.id == "Depends"
                and elt.args
            ):
                arg0 = elt.args[0]
                gate_name = (
                    arg0.id if isinstance(arg0, ast.Name)
                    else arg0.attr if isinstance(arg0, ast.Attribute)
                    else None
                )
                if gate_name in GATE_FUNCTION_NAMES:
                    return True
    return False


def _collect_gate_bearing_routers(tree: ast.Module) -> set[str]:
    """Per-router scope mapping: which `router = APIRouter(deps=[...])`
    assignments carry the gate. A `@router.get(...)` whose receiver name
    is in this set inherits the gate at router level.
    """
    gated: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        call = node.value
        f = call.func
        name = (
            f.id if isinstance(f, ast.Name)
            else f.attr if isinstance(f, ast.Attribute)
            else None
        )
        if name != "APIRouter" or not _apirouter_call_has_gate(call):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                gated.add(tgt.id)
    return gated


def _is_router_method_decorator(deco: ast.expr) -> bool:
    if not isinstance(deco, ast.Call):
        return False
    return isinstance(deco.func, ast.Attribute) and deco.func.attr in ROUTER_METHOD_DECORATORS


def _decorator_receiver_name(deco: ast.Call) -> str | None:
    """For `@router.get(...)` returns `"router"`. Returns None if the
    receiver is not a bare name (e.g., `@self.router.get(...)`).
    """
    if not isinstance(deco.func, ast.Attribute):
        return None
    recv = deco.func.value
    if isinstance(recv, ast.Name):
        return recv.id
    return None


def _function_has_gate_dependency(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    candidates: list[ast.expr] = []
    candidates.extend(func.args.defaults or [])
    candidates.extend(d for d in (func.args.kw_defaults or []) if d is not None)
    for node in candidates:
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = (
            f.id if isinstance(f, ast.Name)
            else f.attr if isinstance(f, ast.Attribute)
            else None
        )
        if name == "Depends" and node.args:
            arg0 = node.args[0]
            gate_name = (
                arg0.id if isinstance(arg0, ast.Name)
                else arg0.attr if isinstance(arg0, ast.Attribute)
                else None
            )
            if gate_name in GATE_FUNCTION_NAMES:
                return True
    return False


def _collect_endpoint_violations(path: Path) -> list[str]:
    tree = _parse(path)
    if tree is None:
        return []
    gated_routers = _collect_gate_bearing_routers(tree)
    rel = _rel(path)
    out: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if not _is_router_method_decorator(deco):
                continue
            recv = _decorator_receiver_name(deco)  # type: ignore[arg-type]
            # Per-router scope: inherit gate ONLY if the specific router
            # instance attached to this decorator was constructed with
            # `dependencies=[Depends(_require_company_id)]`.
            if recv is not None and recv in gated_routers:
                break
            if not _function_has_gate_dependency(node):
                out.append(_violation_key(rel, node.lineno))
            break
    return out


def _scan_all_endpoint_violations() -> set[str]:
    allow = _load_lines(ALLOWLIST_FILE)
    out: set[str] = set()
    for f in _iter_python_files(API_V1_DIR):
        rel = _rel(f)
        rel_app = (
            rel[len("lia-agent-system/"):]
            if rel.startswith("lia-agent-system/")
            else rel
        )
        if rel_app in allow or rel in allow:
            continue
        out.update(_collect_endpoint_violations(f))
    return out


def test_no_endpoint_missing_require_company_id_gate() -> None:
    """Every NEW router endpoint declares `Depends(_require_company_id)`.

    Legacy debt is tracked in `tests/.baseline_endpoint_no_gate.txt`
    (ratchet). Items in `tests/.allowlist_public_endpoints.txt` are
    deliberate public endpoints (health, auth, signed webhooks).
    """
    current = _scan_all_endpoint_violations()
    baseline = _load_lines(BASELINE_ENDPOINT_FILE)
    _assert_no_new_violations(
        current=current,
        baseline=baseline,
        label="endpoint missing _require_company_id gate",
        remediation=(
            "Add `Depends(_require_company_id)` to the endpoint OR — "
            "for legitimately public endpoints — add the file to "
            "`tests/.allowlist_public_endpoints.txt`."
        ),
    )


def test_endpoint_baseline_not_stale() -> None:
    current = _scan_all_endpoint_violations()
    baseline = _load_lines(BASELINE_ENDPOINT_FILE)
    _assert_baseline_in_sync(
        current=current,
        baseline=baseline,
        baseline_file=BASELINE_ENDPOINT_FILE,
        label="endpoint",
    )


# =============================================================================
# (b) Redis tenant namespace inventory — import-aware AST
# =============================================================================

_REDIS_METHODS = {
    "set", "setex", "setnx", "psetex", "get", "mget", "mset",
    "delete", "expire", "hset", "hget", "hmset", "hmget",
    "sadd", "srem", "smembers", "incr", "incrby", "decr",
    "lpush", "rpush", "zadd",
}
_REDIS_RECEIVER_WHITELIST = {
    "redis", "r", "_redis", "redis_client", "redis_conn",
    "cache", "cache_client", "_cache", "rdb", "aredis", "async_redis",
}
# Names of constructors / factories that return a Redis client.
_REDIS_CTOR_NAMES = {
    "Redis", "StrictRedis", "from_url", "ConnectionPool", "Sentinel",
    "RedisCluster", "FakeRedis", "FakeStrictRedis",
}
_REDIS_IMPORT_MODULES = {
    "redis", "aioredis", "redis.asyncio", "redis.client", "redis.cluster",
    "fakeredis",
}
_NAMESPACE_HELPER_NAMES = {
    "tenant_namespaced_key", "tenant_cache_key", "tenant_key",
    "_tenant_key", "build_tenant_key",
}
_REDIS_EXEMPT_PATH_SUBSTRINGS = (
    "tenant_namespaced_key",
    "tenant_redis_namespace",
    "tenant_redis_proxy",
    "/tests/",
    "/migrations/",
    "/scripts/",
)


def _file_imports_redis(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in {"redis", "aioredis", "fakeredis"}:
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in _REDIS_IMPORT_MODULES or mod.split(".")[0] in {
                "redis", "aioredis", "fakeredis",
            }:
                return True
    return False


def _expr_is_namespace_helper_call(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    name = (
        f.id if isinstance(f, ast.Name)
        else f.attr if isinstance(f, ast.Attribute)
        else None
    )
    return name in _NAMESPACE_HELPER_NAMES


def _expr_contains_company_id_placeholder(node: ast.expr) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return "company_id" in node.value or "tenant_id" in node.value
    if isinstance(node, ast.JoinedStr):
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                if "company_id" in part.value or "tenant_id" in part.value:
                    return True
            elif isinstance(part, ast.FormattedValue):
                inner = part.value
                if isinstance(inner, ast.Name) and inner.id in {
                    "company_id", "tenant_id",
                }:
                    return True
                if isinstance(inner, ast.Attribute) and inner.attr in {
                    "company_id", "tenant_id",
                }:
                    return True
        return False
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return _expr_contains_company_id_placeholder(node.left) or (
            _expr_contains_company_id_placeholder(node.right)
        )
    return False


def _key_expr_is_tenant_safe(key_expr: ast.expr) -> bool:
    if _expr_is_namespace_helper_call(key_expr):
        return True
    if _expr_contains_company_id_placeholder(key_expr):
        return True
    if isinstance(key_expr, ast.BinOp):
        return _key_expr_is_tenant_safe(key_expr.left) or _key_expr_is_tenant_safe(
            key_expr.right
        )
    if isinstance(key_expr, ast.Attribute) and (
        key_expr.attr.endswith("_company_key") or key_expr.attr.endswith("_tenant_key")
    ):
        return True
    return False


def _collect_client_assignment_aliases(
    tree: ast.Module, ctor_names: set[str]
) -> set[str]:
    """Scan top-level + function-level Assigns where the RHS is a call
    to a constructor in `ctor_names`. Returns the set of LHS names —
    those variables are now known to be client instances and should be
    treated as valid receivers.

    Catches:
      - `r = Redis(...)`         → "r"
      - `r = redis.from_url(...)` → "r"
      - `r: Redis = Redis(...)`  → "r"  (AnnAssign)
      - `self.r = Redis(...)`    → "r"  (Attribute target)
      - `r1, r2 = make_pair()`   → ignored (no safe way to know)
    """
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value if isinstance(node, ast.Assign) else node.value
            if not isinstance(value, ast.Call):
                continue
            f = value.func
            ctor = (
                f.id if isinstance(f, ast.Name)
                else f.attr if isinstance(f, ast.Attribute)
                else None
            )
            if ctor not in ctor_names:
                continue
            targets = (
                list(node.targets) if isinstance(node, ast.Assign) else [node.target]
            )
            for tgt in targets:
                if isinstance(tgt, ast.Name):
                    aliases.add(tgt.id)
                elif isinstance(tgt, ast.Attribute):
                    aliases.add(tgt.attr)
    return aliases


def _is_client_receiver(
    receiver: ast.expr, whitelist: set[str], aliases: set[str]
) -> bool:
    """Strict receiver match — bare Name in whitelist∪aliases, or
    `self.<name>` / `cls.<name>` where `<name>` is in whitelist∪aliases.

    Attribute chains like `self.redis_pool.client` accept `client` if it
    matches whitelist∪aliases — covers `self.redis_pool.client.set(...)`.
    """
    accepted = whitelist | aliases
    if isinstance(receiver, ast.Name):
        return receiver.id in accepted
    if isinstance(receiver, ast.Attribute):
        # Walk to the final attribute name and check.
        if receiver.attr in accepted:
            return True
    if isinstance(receiver, ast.Call):
        # Chained factory: `get_redis().set(...)` — accept if the called
        # function name itself matches whitelist∪aliases pattern (e.g.,
        # `get_redis_client`, `redis_for`, etc.).
        f = receiver.func
        name = (
            f.id if isinstance(f, ast.Name)
            else f.attr if isinstance(f, ast.Attribute)
            else None
        )
        if name and (name in accepted or name.startswith("get_redis")
                     or name.startswith("get_cache")):
            return True
    return False


class _RedisCallVisitor(ast.NodeVisitor):
    def __init__(self, aliases: set[str]) -> None:
        self.violations: list[int] = []
        self._aliases = aliases

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in _REDIS_METHODS
            and _is_client_receiver(
                node.func.value, _REDIS_RECEIVER_WHITELIST, self._aliases
            )
            and node.args
            and not _key_expr_is_tenant_safe(node.args[0])
        ):
            self.violations.append(node.lineno)
        self.generic_visit(node)


def _scan_all_redis_violations() -> set[str]:
    out: set[str] = set()
    for f in _iter_python_files(APP_DIR):
        rel = _rel(f)
        if any(s in rel for s in _REDIS_EXEMPT_PATH_SUBSTRINGS):
            continue
        tree = _parse(f)
        if tree is None or not _file_imports_redis(tree):
            continue
        aliases = _collect_client_assignment_aliases(tree, _REDIS_CTOR_NAMES)
        visitor = _RedisCallVisitor(aliases)
        visitor.visit(tree)
        for lineno in visitor.violations:
            out.add(_violation_key(rel, lineno))
    return out


def test_no_redis_key_without_tenant_namespace() -> None:
    """Redis key writes/reads in `import redis`/`import aioredis` files use
    `tenant_namespaced_key(...)` or include `company_id`/`tenant_id` in the
    literal f-string.

    Import-aware: only files actually importing a Redis client are
    analyzed. Receiver names limited to a strict whitelist.
    """
    current = _scan_all_redis_violations()
    baseline = _load_lines(BASELINE_REDIS_FILE)
    _assert_no_new_violations(
        current=current,
        baseline=baseline,
        label="Redis key without tenant namespace",
        remediation=(
            "Use `from app.shared.cache import tenant_namespaced_key` and "
            "wrap the key, OR include `{company_id}` / `{tenant_id}` in the "
            "f-string literal."
        ),
    )


def test_redis_baseline_not_stale() -> None:
    current = _scan_all_redis_violations()
    baseline = _load_lines(BASELINE_REDIS_FILE)
    _assert_baseline_in_sync(
        current=current,
        baseline=baseline,
        baseline_file=BASELINE_REDIS_FILE,
        label="Redis",
    )


# =============================================================================
# (c) ES tenant filter inventory — import-aware AST
# =============================================================================

_ES_METHODS = {"search", "count", "msearch", "scroll"}
_ES_RECEIVER_WHITELIST = {
    "es", "_es", "elastic", "elasticsearch", "opensearch", "es_client",
    "elastic_client", "search_client",
}
_ES_CTOR_NAMES = {
    "Elasticsearch", "AsyncElasticsearch", "OpenSearch",
    "AsyncOpenSearch",
}
_ES_IMPORT_MODULES = {"elasticsearch", "opensearchpy"}
_ES_EXEMPT_PATH_SUBSTRINGS = (
    "tenant_aware_es",
    "with_tenant_filter",
    "/tests/",
    "/migrations/",
    "/scripts/",
)


def _file_imports_elasticsearch(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _ES_IMPORT_MODULES:
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in _ES_IMPORT_MODULES:
                return True
    return False


def _is_es_client_receiver(receiver: ast.expr, aliases: set[str]) -> bool:
    return _is_client_receiver(receiver, _ES_RECEIVER_WHITELIST, aliases)


def _expr_is_with_tenant_filter_call(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    name = (
        f.id if isinstance(f, ast.Name)
        else f.attr if isinstance(f, ast.Attribute)
        else None
    )
    return name == "with_tenant_filter"


def _call_body_is_tenant_filtered(call: ast.Call) -> bool:
    for kw in call.keywords or []:
        if kw.arg in {"body", "query"} and _expr_is_with_tenant_filter_call(kw.value):
            return True
    if len(call.args) >= 2 and _expr_is_with_tenant_filter_call(call.args[1]):
        return True
    return False


def _file_uses_tenant_aware_es_client(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "TenantAwareEsClient":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "TenantAwareEsClient":
            return True
    return False


class _EsCallVisitor(ast.NodeVisitor):
    def __init__(self, file_uses_wrapper: bool, aliases: set[str]) -> None:
        self.violations: list[int] = []
        self._wrapper = file_uses_wrapper
        self._aliases = aliases

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in _ES_METHODS
            and _is_es_client_receiver(node.func.value, self._aliases)
            and not (self._wrapper or _call_body_is_tenant_filtered(node))
        ):
            self.violations.append(node.lineno)
        self.generic_visit(node)


def _scan_all_es_violations() -> set[str]:
    out: set[str] = set()
    for f in _iter_python_files(APP_DIR):
        rel = _rel(f)
        if any(s in rel for s in _ES_EXEMPT_PATH_SUBSTRINGS):
            continue
        tree = _parse(f)
        if tree is None or not _file_imports_elasticsearch(tree):
            continue
        aliases = _collect_client_assignment_aliases(tree, _ES_CTOR_NAMES)
        visitor = _EsCallVisitor(
            _file_uses_tenant_aware_es_client(tree), aliases
        )
        visitor.visit(tree)
        for lineno in visitor.violations:
            out.add(_violation_key(rel, lineno))
    return out


def test_no_es_search_without_tenant_filter() -> None:
    """ES search/count/msearch in `import elasticsearch` files wraps the
    body/query in `with_tenant_filter(...)` or uses `TenantAwareEsClient`.
    """
    current = _scan_all_es_violations()
    baseline = _load_lines(BASELINE_ES_FILE)
    _assert_no_new_violations(
        current=current,
        baseline=baseline,
        label="ES search without tenant filter",
        remediation=(
            "Wrap the query with `with_tenant_filter(company_id, query)` "
            "from `app.shared.search.tenant_aware_es_query`, OR refactor "
            "the file to use `TenantAwareEsClient`."
        ),
    )


def test_es_baseline_not_stale() -> None:
    current = _scan_all_es_violations()
    baseline = _load_lines(BASELINE_ES_FILE)
    _assert_baseline_in_sync(
        current=current,
        baseline=baseline,
        baseline_file=BASELINE_ES_FILE,
        label="ES",
    )


# =============================================================================
# (d) Celery task base inventory
# =============================================================================

_CELERY_TASK_DECORATOR_NAMES = {"task", "shared_task"}


def _decorator_is_celery_task(deco: ast.expr) -> bool:
    target = deco.func if isinstance(deco, ast.Call) else deco
    if isinstance(target, ast.Attribute) and target.attr in _CELERY_TASK_DECORATOR_NAMES:
        return True
    if isinstance(target, ast.Name) and target.id in _CELERY_TASK_DECORATOR_NAMES:
        return True
    return False


def _celery_decorator_declares_tenant_aware_base(deco: ast.expr) -> bool:
    if not isinstance(deco, ast.Call):
        return False
    for kw in deco.keywords or []:
        if kw.arg != "base":
            continue
        v = kw.value
        name = (
            v.id if isinstance(v, ast.Name)
            else v.attr if isinstance(v, ast.Attribute)
            else None
        )
        if name == "TenantAwareTask":
            return True
    return False


def test_no_celery_task_without_tenant_aware_base() -> None:
    """Every Celery task in `app/jobs/tasks/**` declares `base=TenantAwareTask`."""
    violations: list[str] = []
    for f in _iter_python_files(JOBS_TASKS_DIR):
        tree = _parse(f)
        if tree is None:
            continue
        rel = _rel(f)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for deco in node.decorator_list:
                if _decorator_is_celery_task(deco):
                    if not _celery_decorator_declares_tenant_aware_base(deco):
                        violations.append(f"{rel}:{node.lineno} {node.name}")
                    break
    assert not violations, (
        "T-1129/S4 sealing — Celery tasks sem `base=TenantAwareTask` "
        f"({len(violations)}). Importe `from app.jobs.tenant_aware_task "
        "import TenantAwareTask` e passe `base=TenantAwareTask` no decorator.\n"
        + "\n".join(violations[:30])
    )


# =============================================================================
# (e) Legacy cross-tenant session usage — AST visit
# =============================================================================


class _LegacyCrossTenantVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.hits: list[tuple[int, str]] = []

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if node.id == "cross_tenant_session_legacy":
            self.hits.append((node.lineno, f"Name `{node.id}`"))
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        if node.attr == "cross_tenant_session_legacy":
            self.hits.append((node.lineno, f"Attribute `.{node.attr}`"))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name == "cross_tenant_session_legacy":
                self.hits.append(
                    (
                        node.lineno,
                        f"from {node.module} import {alias.name}"
                        + (f" as {alias.asname}" if alias.asname else ""),
                    )
                )
        self.generic_visit(node)


def test_no_legacy_cross_tenant_session_usage() -> None:
    """`cross_tenant_session_legacy` should NEVER be imported / referenced.

    Canonical helper is `app.shared.admin.cross_tenant_session` (Task #1148).
    """
    hits: list[str] = []
    for f in _iter_python_files(APP_DIR):
        tree = _parse(f)
        if tree is None:
            continue
        visitor = _LegacyCrossTenantVisitor()
        visitor.visit(tree)
        if not visitor.hits:
            continue
        rel = _rel(f)
        for lineno, what in visitor.hits:
            hits.append(f"{rel}:{lineno} {what}")
    assert not hits, (
        "T-1129/S7 sealing — `cross_tenant_session_legacy` ainda referenciado "
        f"({len(hits)}). Migre para "
        "`app.shared.admin.cross_tenant_session` (audit-logged).\n"
        + "\n".join(hits[:30])
    )


# =============================================================================
# Smoke
# =============================================================================


def test_allowlist_and_baseline_files_exist() -> None:
    for p in [
        ALLOWLIST_FILE,
        BASELINE_ENDPOINT_FILE,
        BASELINE_REDIS_FILE,
        BASELINE_ES_FILE,
    ]:
        assert p.exists(), (
            f"T-1129 sealing — required ratchet/allowlist file missing: {p}"
        )


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
