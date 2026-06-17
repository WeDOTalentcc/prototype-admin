#!/usr/bin/env python3
"""LIA-LLM-1 guardrail: block direct LLM client instantiations outside allowlist.

Nenhum codigo pode instanciar AsyncAnthropic/ChatAnthropic/ChatOpenAI/genai.Client
diretamente — TUDO passa pela camada Choose Your AI (tenant-aware).

Uso:
    python scripts/check_llm_factory_enforcement.py

Exit code 0 se OK, 1 se violacoes encontradas.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "app"
LIBS = ROOT / "libs"

# Arquivos onde instanciacao direta e permitida (implementacoes/helpers autorizados).
# Caminhos RELATIVOS a partir da raiz do backend (lia-agent-system/).
ALLOWLIST = {
    # Implementacoes ABC dos providers — cada um instancia o cliente nativo
    "app/shared/providers/llm_claude.py",
    "app/shared/providers/llm_gemini.py",
    "app/shared/providers/llm_openai.py",
    "app/shared/providers/embedding_gemini.py",
    # LLMService canonical + bootstrap
    "app/domains/ai/services/llm.py",
    "app/shared/llm_bootstrap.py",
    # Helpers tenant-aware (wrappam instanciacao respeitando Choose Your AI)
    "app/shared/tenant_llm_context.py",
    # Endpoint de teste (usa API key fornecida pelo PROPRIO user no body)
    "app/api/v1/llm_config.py",
    # Voice audio transcription (Replit AI Integration — separate billing)
    "app/domains/voice/services/gemini_voice_service.py",
    # Voice live (ja usa get_gemini_client_for_tenant ANTES do import)
    "app/api/v1/gemini_voice.py",
    # Base class do agent (tenant via _get_model com TenantProviderRegistry)
    "libs/agents-core/lia_agents_core/langgraph_react_base.py",
    # Training persona export (fixed version, separate from runtime) — se vierem
    "app/shared/prompts/training_persona.py",
    # Multimodal service — lazy SDK clients gated by bootstrap monkey-patches
    # (bootstrap.install_monkey_patches() instala interceptors em
    # anthropic.AsyncAnthropic.messages.create + genai.aio.models.generate_content
    # ANTES de qualquer instanciacao, garantindo audit trail + tenant-aware
    # billing mesmo via SDK direto). Razao: Camada multimodal precisa de
    # SDK nativo para upload de arquivos + base64 image encoding.
    "app/domains/ai/services/multimodal_service.py",
    # anthropic_client.py — canonical seam factory que wrappam SDK
    # (get_chat_anthropic / get_anthropic_client / get_async_anthropic_client).
    # Espelha o pattern de llm_claude.py (ja allowlisted): este modulo E
    # a fabrica canonical autorizada de instancias Anthropic.
    "app/shared/providers/anthropic_client.py",
    # llm_factory.py — core de create_tracked_llm (Choose Your AI).
    # E a fabrica canonical autorizada que escolhe provider/model conforme
    # tenant policy + faz fallback chain. Espelha llm_bootstrap.py
    # (ja allowlisted): este modulo E a camada Choose Your AI.
    "app/shared/providers/llm_factory.py",
}

# Classes bloqueadas. Chave = nome da classe. Valor = mensagem.
BLOCKED_NAMES = {
    "AsyncAnthropic": "Use get_anthropic_streaming_client_for_tenant() from app.shared.tenant_llm_context",
    "ChatAnthropic": "Use LLMService.get_audited_model() ou get_claude_model_for_tenant()",
    "ChatOpenAI": "Use LLMService (provider=openai) — respeita Choose Your AI",
    "ChatGoogleGenerativeAI": "Use LLMService (provider=gemini) — respeita Choose Your AI",
}

# Tambem bloqueamos chamadas via Attribute do SDK do Gemini (genai.*) fora da
# allowlist. Cobertura ampliada em R-001 (Sprint 1 Quick Wins) para fechar harness
# gap detectado: o bypass de skills_ontology_engine usava genai.configure(...) +
# genai.embed_content(...), que nao eram detectados pelo sensor (so genai.Client).
# Hashimoto: nunca mais bypass via API funcional do google.generativeai.
BLOCKED_ATTRIBUTES = {
    ("genai", "Client"): "Use get_gemini_client_for_tenant() from app.shared.tenant_llm_context",
    (
        "genai",
        "configure",
    ): "Provider gerencia auth tenant-aware — use EmbeddingProviderFactory ou get_provider_for_tenant",
    ("genai", "embed_content"): "Use EmbeddingProviderFactory.get_default().embed_batch() ou .embed_text()",
    ("genai", "GenerativeModel"): "Use get_provider_for_tenant() ou LLMService.get_audited_model() (Choose Your AI)",
    ("genai", "embedding_model"): "Use EmbeddingProviderFactory (allowlisted) em vez do SDK direto",
}


def file_is_allowlisted(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return rel in ALLOWLIST


def check_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line, class_name, message) violations found in path."""
    if file_is_allowlisted(path):
        return []

    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    violations: list[tuple[int, str, str]] = []

    for node in ast.walk(tree):
        # Foco em chamadas (instanciacoes)
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        # Caso 1: Name direto — AsyncAnthropic(...), ChatAnthropic(...), etc.
        if isinstance(func, ast.Name) and func.id in BLOCKED_NAMES:
            violations.append((node.lineno, func.id, BLOCKED_NAMES[func.id]))

        # Caso 2: Attribute — genai.Client(...)
        elif isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                key = (func.value.id, func.attr)
                if key in BLOCKED_ATTRIBUTES:
                    violations.append((node.lineno, f"{func.value.id}.{func.attr}", BLOCKED_ATTRIBUTES[key]))

    return violations


def main() -> int:
    targets: list[Path] = []
    if BACKEND.exists():
        targets.extend(BACKEND.rglob("*.py"))
    if LIBS.exists():
        targets.extend(LIBS.rglob("*.py"))

    # Skip caches
    targets = [p for p in targets if "__pycache__" not in p.parts and ".venv" not in p.parts and "tests" not in p.parts]

    found: list[tuple[Path, int, str, str]] = []
    for path in targets:
        for line, name, msg in check_file(path):
            found.append((path, line, name, msg))

    if not found:
        print("[LLM-FACTORY] OK — nenhuma instanciacao LLM direta fora da allowlist.")
        return 0

    print("[LLM-FACTORY] VIOLACOES (LIA-LLM-1):")
    print("")
    for path, line, name, msg in found:
        rel = path.relative_to(ROOT).as_posix()
        print(f"  {rel}:{line}  {name}()  -> {msg}")
    print("")
    print(f"Total: {len(found)} violacoes.")
    print(
        "Ou migre para a camada Choose Your AI, ou adicione o arquivo a ALLOWLIST em "
        "scripts/check_llm_factory_enforcement.py com justificativa."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
