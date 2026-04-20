"""
Validador end-to-end da configuração do app da LIA no Teams.

Roda uma bateria de checagens contra um ambiente (produção, staging ou local)
para confirmar que tudo o que o smoke test do recrutador depende está no ar.

Cobre os seguintes itens da Task #706:
  - Variáveis de ambiente obrigatórias presentes
  - Endpoint /manifest acessível e bem formado (id estável, validDomains,
    webApplicationInfo, ícones referenciados)
  - Ícones do app servidos com 200
  - Health do bot
  - (opcional) Acquisição do token do Bot Framework com as credenciais reais
    para provar que MICROSOFT_APP_ID/PASSWORD/TENANT batem

Uso:
    python scripts/validate_teams_production.py \\
        --base-url https://ai.wedotalent.cc \\
        [--check-token]   # tenta pegar token via Bot Framework

Sem --check-token, o script só faz GETs públicos contra o backend.
Com --check-token, o script lê MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD e
TEAMS_APP_TENANT_ID do ambiente local (use um .env apontando para os valores
de produção, ou exporte antes de rodar).

Exit code 0 se tudo passar, 1 se houver qualquer falha.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

REQUIRED_ENV_VARS = [
    "MICROSOFT_APP_ID",
    "MICROSOFT_APP_PASSWORD",
    "TEAMS_APP_TENANT_ID",
    "TEAMS_WEBHOOK_SECRET",
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "AZURE_TENANT_ID",
    "WEDOTALENT_PLATFORM_URL",
    "TEAMS_APP_ID",
]

OPTIONAL_ENV_VARS = [
    "TEAMS_BOT_APP_ID",  # falls back to MICROSOFT_APP_ID
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        mark = "PASS" if self.ok else "FAIL"
        return f"  [{mark}] {self.name}" + (f" — {self.detail}" if self.detail else "")


def check_env_vars(strict: bool) -> list[CheckResult]:
    """In strict mode (when --check-token is used) missing env vars fail.
    Otherwise we only report presence — public checks against a remote
    backend do not need the operator to have local creds."""
    results: list[CheckResult] = []
    for var in REQUIRED_ENV_VARS:
        present = bool(os.environ.get(var, "").strip())
        if present:
            results.append(CheckResult(f"env: {var}", True, "present"))
        elif strict:
            results.append(CheckResult(f"env: {var}", False, "missing — required for --check-token"))
        else:
            results.append(CheckResult(f"env: {var}", True, "absent locally (informational; not needed for public checks)"))
    for var in OPTIONAL_ENV_VARS:
        present = bool(os.environ.get(var, "").strip())
        results.append(CheckResult(
            f"env (optional): {var}",
            True,
            "present" if present else "absent (will fall back)",
        ))
    return results


def _unwrap(body: dict[str, Any]) -> dict[str, Any]:
    """Backend wraps responses in {ok, data, meta}; unwrap when present."""
    if isinstance(body, dict) and "data" in body and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def check_health(base_url: str) -> CheckResult:
    url = f"{base_url}/api/v1/teams/health"
    try:
        r = httpx.get(url, timeout=10)
        if r.status_code != 200:
            return CheckResult("teams/health", False, f"HTTP {r.status_code}: {r.text[:120]}")
        body = _unwrap(r.json())
        if body.get("status") != "healthy":
            return CheckResult("teams/health", False, f"status={body.get('status')}")
        if not body.get("bot_configured"):
            return CheckResult("teams/health", False, "bot_configured=false (MICROSOFT_APP_* missing on server)")
        return CheckResult("teams/health", True, "healthy + bot_configured")
    except Exception as e:
        return CheckResult("teams/health", False, str(e))


def check_manifest(base_url: str) -> tuple[CheckResult, dict[str, Any] | None]:
    url = f"{base_url}/api/v1/teams/manifest"
    try:
        r = httpx.get(url, timeout=10)
        if r.status_code != 200:
            return CheckResult("teams/manifest", False, f"HTTP {r.status_code}: {r.text[:200]}"), None
        manifest = r.json()
    except Exception as e:
        return CheckResult("teams/manifest", False, str(e)), None

    issues: list[str] = []

    teams_app_id_env = os.environ.get("TEAMS_APP_ID", "").strip()
    if teams_app_id_env and manifest.get("id") != teams_app_id_env:
        issues.append(f"id mismatch: manifest={manifest.get('id')} env={teams_app_id_env}")

    bots = manifest.get("bots") or []
    if not bots or not bots[0].get("botId"):
        issues.append("bots[0].botId missing")
    else:
        expected_bot = (
            os.environ.get("TEAMS_BOT_APP_ID")
            or os.environ.get("MICROSOFT_APP_ID")
            or ""
        ).strip()
        if expected_bot and bots[0]["botId"] != expected_bot:
            issues.append(f"botId mismatch: manifest={bots[0]['botId']} env={expected_bot}")

    valid_domains = manifest.get("validDomains") or []
    expected_domain = urlparse(base_url).netloc
    if expected_domain not in valid_domains:
        issues.append(f"validDomains missing platform domain {expected_domain}")

    azure_client_id = os.environ.get("AZURE_CLIENT_ID", "").strip()
    wai = manifest.get("webApplicationInfo")
    if azure_client_id:
        if not wai or wai.get("id") != azure_client_id:
            issues.append("webApplicationInfo.id does not match AZURE_CLIENT_ID — SSO will fail")
        elif not wai.get("resource", "").startswith(f"api://{expected_domain}/"):
            issues.append(f"webApplicationInfo.resource should be api://{expected_domain}/<AZURE_CLIENT_ID>")
    else:
        if wai:
            issues.append("webApplicationInfo present without AZURE_CLIENT_ID — SSO will fail silently")

    icons = manifest.get("icons") or {}
    if not icons.get("color") or not icons.get("outline"):
        issues.append("icons.color/outline missing")

    ok = not issues
    return CheckResult(
        "teams/manifest",
        ok,
        "structure ok" if ok else "; ".join(issues),
    ), manifest


def check_icons(base_url: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name in ("wedo-color.png", "wedo-outline.png"):
        url = f"{base_url}/teams-icons/{name}"
        try:
            r = httpx.get(url, timeout=10)
            ok = r.status_code == 200 and r.headers.get("content-type", "").startswith("image/")
            results.append(CheckResult(
                f"icon: {name}",
                ok,
                f"HTTP {r.status_code} ({len(r.content)} bytes)" if ok else f"HTTP {r.status_code}",
            ))
        except Exception as e:
            results.append(CheckResult(f"icon: {name}", False, str(e)))
    return results


def check_bot_token() -> CheckResult:
    """Acquire a Bot Framework token using the configured creds — proves they work end-to-end."""
    app_id = os.environ.get("MICROSOFT_APP_ID", "").strip()
    app_password = os.environ.get("MICROSOFT_APP_PASSWORD", "").strip()
    tenant_id = (
        os.environ.get("TEAMS_APP_TENANT_ID", "").strip()
        or os.environ.get("AZURE_TENANT_ID", "").strip()
    )
    if not (app_id and app_password and tenant_id):
        return CheckResult("bot framework token", False, "missing MICROSOFT_APP_ID / MICROSOFT_APP_PASSWORD / TEAMS_APP_TENANT_ID")

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    try:
        r = httpx.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": app_id,
                "client_secret": app_password,
                "scope": "https://api.botframework.com/.default",
            },
            timeout=10,
        )
        if r.status_code != 200:
            return CheckResult("bot framework token", False, f"HTTP {r.status_code}: {r.text[:200]}")
        token = r.json().get("access_token")
        if not token:
            return CheckResult("bot framework token", False, "no access_token in response")
        return CheckResult("bot framework token", True, "acquired ok (creds + tenant valid)")
    except Exception as e:
        return CheckResult("bot framework token", False, str(e))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", required=True, help="e.g. https://ai.wedotalent.cc")
    parser.add_argument("--check-token", action="store_true", help="also acquire Bot Framework token using local env")
    parser.add_argument("--print-manifest", action="store_true", help="print the fetched manifest at the end")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    print(f"\nValidating Teams production setup against {base_url}\n")

    if args.check_token:
        print("Environment variables (local process — required for --check-token):")
    else:
        print("Environment variables (local process — informational; only enforced with --check-token):")
    env_results = check_env_vars(strict=args.check_token)
    for r in env_results:
        print(r.render())

    print("\nBackend endpoints:")
    health_result = check_health(base_url)
    print(health_result.render())

    manifest_result, manifest = check_manifest(base_url)
    print(manifest_result.render())

    icon_results = check_icons(base_url)
    for r in icon_results:
        print(r.render())

    token_result: CheckResult | None = None
    if args.check_token:
        print("\nBot Framework auth:")
        token_result = check_bot_token()
        print(token_result.render())

    all_results = env_results + [health_result, manifest_result] + icon_results
    if token_result:
        all_results.append(token_result)

    failures = [r for r in all_results if not r.ok]
    print(f"\nSummary: {len(all_results) - len(failures)}/{len(all_results)} checks passed")
    if failures:
        print("Failures:")
        for r in failures:
            print(r.render())

    if args.print_manifest and manifest is not None:
        print("\nManifest:")
        print(json.dumps(manifest, indent=2, ensure_ascii=False))

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
