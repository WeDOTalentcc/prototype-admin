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


# YAML files in prompts/domains/ that are NOT LLM prompt files (no system_prompt/metadata)
# and should be skipped by the prompt validator.
_NON_PROMPT_YAML_FILES: frozenset[str] = frozenset({
    "automation_templates.yaml",   # Sprint B: template collection (data, not LLM prompt)
    "onboarding_questions.yaml",   # P2-2: Q&A config for onboarding (data, not LLM prompt)
})


def validate_all_prompts(prompts_dir: Path | None = None) -> dict[str, list[str]]:
    """
    Valida todos os prompts YAML. Retorna dict {filename: [errors]}.
    Dict vazio = todos válidos.
    Ignora arquivos em _NON_PROMPT_YAML_FILES (config/data YAMLs, não prompts LLM).
    """
    directory = prompts_dir or _PROMPTS_DIR
    issues: dict[str, list[str]] = {}
    try:
        for yaml_file in sorted(directory.glob("*.yaml")):
            if yaml_file.name in _NON_PROMPT_YAML_FILES:
                continue
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
                if system_prompt:
                    prompt_version_registry.register(
                        name=domain,
                        version=str(version),
                        template=system_prompt,
                    )
                    count += 1
                    continue

                prompts_block = data.get("prompts")
                if isinstance(prompts_block, dict):
                    for prompt_name, prompt_text in prompts_block.items():
                        if isinstance(prompt_text, str) and prompt_text.strip():
                            prompt_version_registry.register(
                                name=f"{domain}/{prompt_name}",
                                version=str(version),
                                template=prompt_text,
                            )
                            count += 1
                    continue

                variants_block = data.get("variants")
                if isinstance(variants_block, (dict, list)):
                    exp_id = data.get("experiment_id", yaml_file.stem)
                    items = (
                        variants_block.items() if isinstance(variants_block, dict)
                        else ((v.get("variant_id", f"v{i}"), v) for i, v in enumerate(variants_block) if isinstance(v, dict))
                    )
                    for variant_name, variant_data in items:
                        tmpl = variant_data if isinstance(variant_data, str) else ""
                        if not tmpl and isinstance(variant_data, dict):
                            tmpl = variant_data.get("system_prompt", "") or variant_data.get("prompt_text", "")
                        if tmpl:
                            prompt_version_registry.register(
                                name=f"experiment/{exp_id}/{variant_name}",
                                version=str(version),
                                template=tmpl,
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


def bootstrap_experiments_from_yaml() -> int:
    """Bootstrap A/B experiments from YAML files in the experiments directory.

    Reads experiment YAML files that define variants with system_prompt fields
    and creates experiments via ExperimentManager.create_experiment_from_yaml().
    Returns the number of experiments created.
    """
    from app.shared.ab_testing import get_experiment_manager

    manager = get_experiment_manager()
    created = 0

    if not _EXPERIMENTS_DIR.exists():
        return 0

    for yaml_file in sorted(_EXPERIMENTS_DIR.glob("*.yaml")):
        try:
            data = load_prompt_yaml(yaml_file)
            variants_block = data.get("variants")
            if not isinstance(variants_block, (dict, list)) or len(variants_block) < 2:
                continue

            exp_id = data.get("experiment_id", yaml_file.stem)
            description = data.get("description", "")

            variant_prompts: dict[str, str] = {}
            items = (
                variants_block.items() if isinstance(variants_block, dict)
                else ((v.get("variant_id", f"v{i}"), v) for i, v in enumerate(variants_block) if isinstance(v, dict))
            )
            for variant_name, variant_data in items:
                tmpl = variant_data if isinstance(variant_data, str) else ""
                if not tmpl and isinstance(variant_data, dict):
                    tmpl = variant_data.get("system_prompt", "") or variant_data.get("prompt_text", "")
                if tmpl:
                    variant_prompts[variant_name] = tmpl

            if len(variant_prompts) >= 2:
                manager.create_experiment(
                    name=exp_id,
                    variants=variant_prompts,
                    description=description,
                )
                created += 1
                logger.info("[PromptVersionLoader] Bootstrapped experiment '%s' with %d variants",
                            exp_id, len(variant_prompts))
        except Exception as exc:
            logger.warning("[PromptVersionLoader] Failed to bootstrap experiment from %s: %s",
                          yaml_file.name, exc)

    return created
