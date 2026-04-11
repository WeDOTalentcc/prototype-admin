"""
Prompt Version Loader — Z3-02.

Carrega e valida arquivos YAML de system prompts.
Garante que todos os prompts têm os campos obrigatórios: version e updated_at.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "domains"

REQUIRED_METADATA_FIELDS = {"version", "domain"}
OPTIONAL_METADATA_FIELDS = {"updated_at", "description", "author"}


@dataclass
class PromptVersionInfo:
    domain: str
    version: str
    updated_at: str | None
    description: str | None
    has_system_prompt: bool
    file_path: str


def load_prompt_yaml(file_path: str | Path) -> dict[str, Any]:
    """Carrega um YAML de prompt e retorna o dict parsed."""
    try:
        import yaml
    except ImportError:
        import json  # fallback básico
        with open(file_path) as f:
            return json.load(f)

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def validate_prompt_metadata(data: dict[str, Any], file_path: str = "") -> list[str]:
    """
    Valida metadados obrigatórios do prompt YAML.

    Suporta dois formatos:
      - Novo (metadata block): `metadata.version` + `metadata.domain`
      - Legado (root level): `version` + `domain` no nível raiz

    Returns lista de erros (vazia = válido).
    """
    errors = []
    metadata = data.get("metadata", {}) or {}

    for field in REQUIRED_METADATA_FIELDS:
        # Accept field in metadata block OR at root level (legacy flat format)
        if not metadata.get(field) and not data.get(field):
            errors.append(f"[{file_path}] metadata.{field} ausente ou vazio")

    if not data.get("system_prompt"):
        errors.append(f"[{file_path}] system_prompt ausente ou vazio")

    return errors


def get_prompt_version_info(file_path: str | Path) -> PromptVersionInfo | None:
    """Retorna VersionInfo de um arquivo de prompt YAML. Suporta formato legado e novo."""
    try:
        data = load_prompt_yaml(file_path)
        metadata = data.get("metadata", {}) or {}
        # Support both nested metadata block and flat root-level fields
        domain = metadata.get("domain") or data.get("domain", "unknown")
        version = metadata.get("version") or data.get("version", "0.0")
        updated_at = metadata.get("updated_at") or data.get("updated_at")
        description = metadata.get("description") or data.get("description")
        return PromptVersionInfo(
            domain=domain,
            version=version,
            updated_at=updated_at,
            description=description,
            has_system_prompt=bool(data.get("system_prompt")),
            file_path=str(file_path),
        )
    except Exception as exc:
        logger.debug("[PromptVersionLoader] erro ao ler %s: %s", file_path, exc)
        return None


def list_all_prompt_versions(prompts_dir: Path | None = None) -> list[PromptVersionInfo]:
    """Lista versões de todos os prompts YAML no diretório de domínios."""
    directory = prompts_dir or _PROMPTS_DIR
    results = []
    try:
        for yaml_file in sorted(directory.glob("*.yaml")):
            info = get_prompt_version_info(yaml_file)
            if info:
                results.append(info)
    except Exception as exc:
        logger.warning("[PromptVersionLoader] erro ao listar prompts: %s", exc)
    return results


def validate_all_prompts(prompts_dir: Path | None = None) -> dict[str, list[str]]:
    """
    Valida todos os prompts YAML. Retorna dict {filename: [errors]}.
    Dict vazio = todos válidos.
    """
    directory = prompts_dir or _PROMPTS_DIR
    issues: dict[str, list[str]] = {}
    try:
        for yaml_file in sorted(directory.glob("*.yaml")):
            data = load_prompt_yaml(yaml_file)
            errors = validate_prompt_metadata(data, file_path=yaml_file.name)
            if errors:
                issues[yaml_file.name] = errors
    except Exception as exc:
        logger.warning("[PromptVersionLoader] validate_all falhou: %s", exc)
    return issues


_SHARED_DIR = Path(__file__).parent.parent / "prompts" / "shared"
_EXPERIMENTS_DIR = Path(__file__).parent.parent / "prompts" / "experiments"


def register_all_prompts_at_startup() -> int:
    """Register all YAML prompts into PromptVersionRegistry at startup.

    Scans domains/, shared/, and experiments/ directories. Returns count of
    prompts registered.
    """
    from app.domains.ai.services.prompt_version_registry import prompt_version_registry

    count = 0
    dirs = [_PROMPTS_DIR, _SHARED_DIR, _EXPERIMENTS_DIR]

    for directory in dirs:
        if not directory.exists():
            continue
        for yaml_file in sorted(directory.glob("*.yaml")):
            try:
                data = load_prompt_yaml(yaml_file)
                metadata = data.get("metadata", {}) or {}
                domain = metadata.get("domain") or data.get("domain", yaml_file.stem)
                version = metadata.get("version") or data.get("version", "1.0")
                system_prompt = data.get("system_prompt", "")
                if not system_prompt:
                    continue
                prompt_version_registry.register(
                    name=domain,
                    version=str(version),
                    template=system_prompt,
                )
                count += 1
            except Exception as exc:
                logger.warning(
                    "[PromptVersionLoader] Failed to register %s: %s",
                    yaml_file.name, exc,
                )

    logger.info(
        "[PromptVersionLoader] Registered %d prompts from YAML files into PromptVersionRegistry",
        count,
    )
    return count
