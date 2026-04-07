"""
Prompt Registry with Versioning Support.

This module provides a centralized registry for managing prompts with version control,
allowing tracking of changes, comparing versions, and retrieving specific versions.

YAML-first loading: prompts are loaded from YAML files in app/prompts/ when available.
Fallback to Python-defined prompts with a warning log when YAML is not found.
"""

import difflib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """Represents a specific version of a prompt."""
    version: str
    content: str
    created_at: datetime
    author: str
    changelog: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "version": self.version,
            "content_length": len(self.content),
            "created_at": self.created_at.isoformat(),
            "author": self.author,
            "changelog": self.changelog
        }


@dataclass
class PromptMetadata:
    """Metadata for a prompt across all versions."""
    name: str
    description: str = ""
    agent_number: int | None = None
    versions: dict[str, PromptVersion] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    few_shot_examples: list[dict[str, Any]] = field(default_factory=list)

    @property
    def latest_version(self) -> str | None:
        """Get the latest version string."""
        if not self.versions:
            return None
        return max(self.versions.keys(), key=self._parse_version)
    
    @staticmethod
    def _parse_version(version: str) -> tuple:
        """Parse version string to tuple for comparison."""
        try:
            parts = version.split(".")
            return tuple(int(p) for p in parts)
        except (ValueError, AttributeError):
            return (0, 0, 0)


class PromptRegistry:
    """Registro centralizado de prompts com versionamento."""
    
    def __init__(self):
        self._prompts: dict[str, PromptMetadata] = {}
        self._initialized: bool = False
    
    def register_prompt(
        self,
        name: str,
        content: str,
        version: str = "1.0.0",
        author: str = "system",
        changelog: str = "Initial version",
        description: str = "",
        agent_number: int | None = None
    ) -> None:
        """
        Registra nova versão de prompt.
        
        Args:
            name: Nome único do prompt (snake_case)
            content: Conteúdo completo do prompt
            version: Versão semântica (X.Y.Z)
            author: Autor da versão
            changelog: Descrição das mudanças
            description: Descrição geral do prompt
            agent_number: Número do agente (opcional)
        """
        if name not in self._prompts:
            self._prompts[name] = PromptMetadata(
                name=name,
                description=description,
                agent_number=agent_number
            )
        
        prompt_version = PromptVersion(
            version=version,
            content=content,
            created_at=datetime.now(),
            author=author,
            changelog=changelog
        )
        
        self._prompts[name].versions[version] = prompt_version
        
        if description:
            self._prompts[name].description = description
        if agent_number is not None:
            self._prompts[name].agent_number = agent_number
    
    def get_prompt(self, name: str, version: str = "latest") -> str | None:
        """
        Retorna prompt por nome e versão.
        
        Args:
            name: Nome do prompt
            version: Versão específica ou "latest" para a mais recente
            
        Returns:
            Conteúdo do prompt ou None se não encontrado
        """
        if name not in self._prompts:
            return None
        
        metadata = self._prompts[name]
        
        if version == "latest":
            version = metadata.latest_version
            if version is None:
                return None
        
        prompt_version = metadata.versions.get(version)
        return prompt_version.content if prompt_version else None
    
    def get_prompt_version(self, name: str, version: str = "latest") -> PromptVersion | None:
        """
        Retorna objeto PromptVersion completo.
        
        Args:
            name: Nome do prompt
            version: Versão específica ou "latest"
            
        Returns:
            PromptVersion ou None se não encontrado
        """
        if name not in self._prompts:
            return None
        
        metadata = self._prompts[name]
        
        if version == "latest":
            version = metadata.latest_version
            if version is None:
                return None
        
        return metadata.versions.get(version)
    
    def get_all_versions(self, name: str) -> list[str]:
        """
        Lista todas as versões de um prompt.
        
        Args:
            name: Nome do prompt
            
        Returns:
            Lista de versões ordenadas (mais antiga primeiro)
        """
        if name not in self._prompts:
            return []
        
        versions = list(self._prompts[name].versions.keys())
        return sorted(versions, key=PromptMetadata._parse_version)
    
    def get_catalog(self) -> dict[str, Any]:
        """
        Retorna catálogo completo de prompts.
        
        Returns:
            Dicionário com todos os prompts e suas versões
        """
        catalog = {}
        
        for name, metadata in self._prompts.items():
            catalog[name] = {
                "name": name,
                "description": metadata.description,
                "agent_number": metadata.agent_number,
                "latest_version": metadata.latest_version,
                "total_versions": len(metadata.versions),
                "versions": {
                    v: pv.to_dict() 
                    for v, pv in metadata.versions.items()
                }
            }
        
        return catalog
    
    def compare_versions(self, name: str, v1: str, v2: str) -> dict[str, Any]:
        """
        Compara duas versões de um prompt.
        
        Args:
            name: Nome do prompt
            v1: Primeira versão
            v2: Segunda versão
            
        Returns:
            Dicionário com diff e estatísticas
        """
        if name not in self._prompts:
            return {"error": f"Prompt '{name}' não encontrado"}
        
        metadata = self._prompts[name]
        
        pv1 = metadata.versions.get(v1)
        pv2 = metadata.versions.get(v2)
        
        if not pv1:
            return {"error": f"Versão '{v1}' não encontrada"}
        if not pv2:
            return {"error": f"Versão '{v2}' não encontrada"}
        
        lines1 = pv1.content.splitlines(keepends=True)
        lines2 = pv2.content.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=f"{name} v{v1}",
            tofile=f"{name} v{v2}",
            lineterm=""
        ))
        
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        return {
            "prompt_name": name,
            "version_from": v1,
            "version_to": v2,
            "diff": "".join(diff),
            "statistics": {
                "additions": additions,
                "deletions": deletions,
                "lines_v1": len(lines1),
                "lines_v2": len(lines2),
                "chars_v1": len(pv1.content),
                "chars_v2": len(pv2.content)
            },
            "metadata": {
                "v1_author": pv1.author,
                "v1_date": pv1.created_at.isoformat(),
                "v1_changelog": pv1.changelog,
                "v2_author": pv2.author,
                "v2_date": pv2.created_at.isoformat(),
                "v2_changelog": pv2.changelog
            }
        }
    
    def list_prompts(self) -> list[str]:
        """
        Lista todos os nomes de prompts registrados.
        
        Returns:
            Lista de nomes de prompts
        """
        return list(self._prompts.keys())
    
    def get_prompt_metadata(self, name: str) -> dict[str, Any] | None:
        """
        Retorna metadata de um prompt específico.
        
        Args:
            name: Nome do prompt
            
        Returns:
            Dicionário com metadata ou None
        """
        if name not in self._prompts:
            return None
        
        metadata = self._prompts[name]
        return {
            "name": metadata.name,
            "description": metadata.description,
            "agent_number": metadata.agent_number,
            "latest_version": metadata.latest_version,
            "versions": self.get_all_versions(name)
        }

    def get_variables(self, name: str) -> dict[str, Any]:
        """
        Returns template variables for the named prompt (loaded from YAML).

        Variables are key-value pairs that can be interpolated into the prompt
        at runtime using ``render_prompt()``.

        Args:
            name: Prompt registry key

        Returns:
            Dict of variable name → default value (empty dict if none defined)
        """
        meta = self._prompts.get(name)
        return dict(meta.variables) if meta else {}

    def get_few_shot_examples(self, name: str) -> list[dict[str, Any]]:
        """
        Returns few-shot examples for the named prompt (loaded from YAML).

        Each example is a dict with at least ``input`` and ``output`` keys,
        representing a sample turn the agent should emulate.

        Args:
            name: Prompt registry key

        Returns:
            List of example dicts (empty list if none defined)
        """
        meta = self._prompts.get(name)
        return list(meta.few_shot_examples) if meta else []

    def render_prompt(
        self,
        name: str,
        variables: dict[str, Any] | None = None,
        version: str = "latest",
    ) -> str | None:
        """
        Render the prompt by interpolating runtime variables.

        Variable placeholders use Python ``str.format_map`` syntax:
        ``{variable_name}``. YAML-defined default values are used for any
        variable not supplied at call time.

        Args:
            name: Prompt registry key
            variables: Runtime overrides; merged over YAML defaults
            version: Prompt version (default: latest)

        Returns:
            Rendered prompt string, or None if prompt not found
        """
        content = self.get_prompt(name, version=version)
        if content is None:
            return None

        meta = self._prompts.get(name)
        defaults = dict(meta.variables) if meta else {}
        merged = {**defaults, **(variables or {})}

        if not merged:
            return content

        try:
            return content.format_map(merged)
        except KeyError as exc:
            _logger.warning(
                f"render_prompt('{name}'): missing variable {exc} — "
                "returning unrendered content"
            )
            return content

    def is_initialized(self) -> bool:
        """Check if the registry has been initialized."""
        return self._initialized

    def mark_initialized(self) -> None:
        """Mark the registry as initialized."""
        self._initialized = True

    def load_from_yaml(
        self,
        yaml_path: str,
        name: str | None = None,
        version: str = "1.0.0",
        author: str = "yaml",
        changelog: str = "Loaded from YAML",
        description: str = "",
        agent_number: int | None = None,
    ) -> bool:
        """
        Load a prompt from a YAML file (YAML-first strategy).

        The YAML file must have a 'system_prompt' key at the top level,
        or a 'prompts.<name>' key for shared multi-prompt files.

        Args:
            yaml_path: Path to the YAML file (absolute or relative to app/prompts/)
            name: Registry key for this prompt. Defaults to YAML file stem.
            version: Semantic version string
            author: Author label
            changelog: Description of this version
            description: Human-readable description
            agent_number: Optional agent number for ordering

        Returns:
            True if loaded successfully, False on failure (with warning log).
        """
        try:
            import yaml

            path = Path(yaml_path)
            if not path.is_absolute():
                prompts_root = Path(__file__).parent.parent.parent / "prompts"
                path = prompts_root / yaml_path
                if not path.suffix:
                    path = path.with_suffix(".yaml")

            if not path.exists():
                _logger.warning(
                    f"YAML prompt not found: {path} — falling back to Python-defined prompt"
                )
                return False

            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            prompt_name = name or path.stem
            content = data.get("system_prompt", "")

            if not content:
                _logger.warning(
                    f"YAML {path} has no 'system_prompt' key — "
                    f"falling back to Python-defined prompt for '{prompt_name}'"
                )
                return False

            meta_block = data.get("metadata", {})
            resolved_version = meta_block.get("version", version)
            resolved_description = (
                description
                or meta_block.get("description", "")
                or data.get("description", "")
            )

            self.register_prompt(
                name=prompt_name,
                content=content,
                version=resolved_version,
                author=author,
                changelog=changelog,
                description=resolved_description,
                agent_number=agent_number,
            )

            if prompt_name in self._prompts:
                meta = self._prompts[prompt_name]
                variables = data.get("variables", {})
                if isinstance(variables, dict):
                    meta.variables = variables
                few_shot = data.get("few_shot_examples", [])
                if isinstance(few_shot, list):
                    meta.few_shot_examples = few_shot
                if variables:
                    _logger.info(
                        f"  Loaded {len(variables)} variables for '{prompt_name}'"
                    )
                if few_shot:
                    _logger.info(
                        f"  Loaded {len(few_shot)} few-shot examples for '{prompt_name}'"
                    )

            _logger.info(f"Loaded prompt '{prompt_name}' from YAML: {path.name}")
            return True

        except Exception as exc:
            _logger.warning(
                f"Failed to load YAML prompt '{yaml_path}': {exc} — "
                "falling back to Python-defined prompt"
            )
            return False

    def get_or_fallback(
        self,
        name: str,
        fallback_content: str,
        version: str = "1.0.0",
        yaml_path: str | None = None,
    ) -> str:
        """
        Get a prompt by name, trying YAML first, then fallback_content.

        If the prompt is not yet registered, attempts to load from YAML
        (if yaml_path provided), then registers fallback_content with a
        warning log if YAML loading fails.

        Args:
            name: Prompt registry key
            fallback_content: Python-defined prompt string (fallback)
            version: Version for fallback registration
            yaml_path: Optional YAML path override

        Returns:
            Prompt content string
        """
        existing = self.get_prompt(name)
        if existing:
            return existing

        if yaml_path:
            loaded = self.load_from_yaml(yaml_path, name=name, version=version)
            if loaded:
                content = self.get_prompt(name)
                if content:
                    return content

        _logger.warning(
            f"Prompt '{name}' not found in YAML — using Python-defined fallback. "
            "Migrate to YAML for better versioning and A/B testing support."
        )
        self.register_prompt(
            name=name,
            content=fallback_content,
            version=version,
            author="python_fallback",
            changelog="Python-defined fallback (YAML migration pending)",
        )
        return fallback_content


prompt_registry = PromptRegistry()


def init_prompts() -> None:
    """
    Inicializa o registro com todos os prompts existentes.

    Estratégia YAML-first: tenta carregar de YAML; usa fallback Python com warning
    se o YAML não existir ou não tiver 'system_prompt'.

    Esta função deve ser chamada uma vez na inicialização da aplicação.
    """
    if prompt_registry.is_initialized():
        return

    from app.shared.prompts.agent_prompts import (
        ANALYST_FEEDBACK_PROMPT,
        ATS_INTEGRATOR_PROMPT,
        CV_SCREENING_PROMPT,
        DATA_PERSISTENCE_GUIDELINES,
        ETHICAL_GUIDELINES,
        HR_VOCABULARY,
        INTERVIEWER_PROMPT,
        JOB_PLANNER_PROMPT,
        LIA_PERSONA,
        ORCHESTRATOR_PROMPT,
        PROACTIVE_INSIGHTS_PROMPT,
        RECRUITER_ASSISTANT_PROMPT,
        SCHEDULING_PROMPT,
        SOURCING_PROMPT,
        WSI_EVALUATOR_PROMPT,
    )

    _domain_prompts: list[tuple[str, str, str, int | None]] = [
        ("orchestrator", "domains/orchestrator", ORCHESTRATOR_PROMPT, 0),
        ("job_planner", "domains/job_management", JOB_PLANNER_PROMPT, 1),
        ("sourcing", "domains/sourcing", SOURCING_PROMPT, 2),
        ("cv_screening", "domains/cv_screening", CV_SCREENING_PROMPT, 3),
        ("interviewer", "domains/wsi_interview", INTERVIEWER_PROMPT, 4),
        ("wsi_evaluator", "domains/wsi_evaluation", WSI_EVALUATOR_PROMPT, 5),
        ("scheduling", "domains/interview_scheduling", SCHEDULING_PROMPT, 6),
        ("analyst_feedback", "domains/analytics", ANALYST_FEEDBACK_PROMPT, 7),
        ("ats_integrator", "domains/ats_integration", ATS_INTEGRATOR_PROMPT, 8),
        ("recruiter_assistant", "domains/recruiter_assistant", RECRUITER_ASSISTANT_PROMPT, 9),
        ("proactive_insights", "domains/analysis", PROACTIVE_INSIGHTS_PROMPT, 10),
    ]

    for name, yaml_path, fallback, agent_num in _domain_prompts:
        loaded = prompt_registry.load_from_yaml(
            yaml_path=yaml_path,
            name=name,
            version="2.0.0",
            author="yaml",
            changelog="Loaded from YAML (YAML-first strategy)",
            agent_number=agent_num,
        )
        if not loaded:
            _logger.warning(
                f"[PromptRegistry] Prompt '{name}' loaded from Python fallback — "
                f"migrate to YAML at app/prompts/{yaml_path}.yaml"
            )
            prompt_registry.register_prompt(
                name=name,
                content=fallback,
                version="2.0.0",
                author="python_fallback",
                changelog="Python-defined fallback (YAML migration pending)",
                agent_number=agent_num,
            )

    _shared_prompts: list[tuple[str, str]] = [
        ("lia_persona", LIA_PERSONA),
        ("hr_vocabulary", HR_VOCABULARY),
        ("data_persistence_guidelines", DATA_PERSISTENCE_GUIDELINES),
        ("ethical_guidelines", ETHICAL_GUIDELINES),
    ]

    for name, content in _shared_prompts:
        prompt_registry.register_prompt(
            name=name,
            content=content,
            version="2.0.0",
            author="wedotalent",
            changelog="Shared component — loaded from YAML-backed Python module",
        )

    prompt_registry.mark_initialized()


def get_prompt_from_registry(name: str, version: str = "latest", context: str = "") -> str | None:
    """
    Convenience function to get a prompt with context substitution.
    
    Args:
        name: Nome do prompt
        version: Versão específica ou "latest"
        context: Contexto a ser substituído no placeholder {context}
        
    Returns:
        Prompt com contexto substituído ou None
    """
    if not prompt_registry.is_initialized():
        init_prompts()
    
    content = prompt_registry.get_prompt(name, version)
    if content is None:
        return None
    
    return content.format(context=context or "Nenhum contexto adicional")
