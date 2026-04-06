"""
Prompt Registry with Versioning Support.

This module provides a centralized registry for managing prompts with version control,
allowing tracking of changes, comparing versions, and retrieving specific versions.
"""

import difflib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


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
    
    def is_initialized(self) -> bool:
        """Check if the registry has been initialized."""
        return self._initialized
    
    def mark_initialized(self) -> None:
        """Mark the registry as initialized."""
        self._initialized = True


prompt_registry = PromptRegistry()


def init_prompts() -> None:
    """
    Inicializa o registro com todos os prompts existentes.
    
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
    
    prompt_registry.register_prompt(
        name="orchestrator",
        content=ORCHESTRATOR_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionada persona LIA, vocabulário HR, persistência de dados",
        description="Orquestrador central que coordena todos os agentes especializados",
        agent_number=0
    )
    
    prompt_registry.register_prompt(
        name="job_planner",
        content=JOB_PLANNER_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionada metodologia WSI, campos de persistência, formato estruturado",
        description="Especialista em definição e estruturação de vagas",
        agent_number=1
    )
    
    prompt_registry.register_prompt(
        name="sourcing",
        content=SOURCING_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionado fluxo de busca dual, persistência de candidatos, outreach",
        description="Especialista em busca e captação de candidatos",
        agent_number=2
    )
    
    prompt_registry.register_prompt(
        name="cv_screening",
        content=CV_SCREENING_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionada metodologia de scoring, red flags, campos de persistência",
        description="Especialista em análise de CVs e screening inicial",
        agent_number=3
    )
    
    prompt_registry.register_prompt(
        name="interviewer",
        content=INTERVIEWER_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionada metodologia CBI/STAR, adaptação dinâmica, coleta de dados sensíveis",
        description="Especialista em entrevistas estruturadas WSI",
        agent_number=4
    )
    
    prompt_registry.register_prompt(
        name="wsi_evaluator",
        content=WSI_EVALUATOR_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionada metodologia Bloom+Dreyfus+BigFive, comparação side-by-side",
        description="Especialista em avaliação científica de candidatos",
        agent_number=5
    )
    
    prompt_registry.register_prompt(
        name="scheduling",
        content=SCHEDULING_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionada integração Microsoft Graph, status de agendamento",
        description="Especialista em agendamento de entrevistas",
        agent_number=6
    )
    
    prompt_registry.register_prompt(
        name="analyst_feedback",
        content=ANALYST_FEEDBACK_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionados KPIs, relatórios de funil, feedback estruturado",
        description="Especialista em KPIs, relatórios e comunicação",
        agent_number=7
    )
    
    prompt_registry.register_prompt(
        name="ats_integrator",
        content=ATS_INTEGRATOR_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionadas regras de sincronização, mapeamento Gupy/Pandapé",
        description="Especialista em integração com sistemas ATS",
        agent_number=8
    )
    
    prompt_registry.register_prompt(
        name="recruiter_assistant",
        content=RECRUITER_ASSISTANT_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionado daily briefing, calibração, acompanhamento de metas",
        description="Assistente pessoal do recrutador para tarefas do dia-a-dia",
        agent_number=9
    )
    
    prompt_registry.register_prompt(
        name="proactive_insights",
        content=PROACTIVE_INSIGHTS_PROMPT,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Adicionadas regras de análise, formato de insights estruturado",
        description="Gerador de insights proativos para buscas de candidatos",
        agent_number=10
    )
    
    prompt_registry.register_prompt(
        name="lia_persona",
        content=LIA_PERSONA,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Persona unificada para todos os agentes",
        description="Componente compartilhado: Identidade e tom de comunicação da LIA"
    )
    
    prompt_registry.register_prompt(
        name="hr_vocabulary",
        content=HR_VOCABULARY,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Vocabulário técnico de RH brasileiro padronizado",
        description="Componente compartilhado: Termos técnicos de RH"
    )
    
    prompt_registry.register_prompt(
        name="data_persistence_guidelines",
        content=DATA_PERSISTENCE_GUIDELINES,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Diretrizes de persistência e sincronização ATS",
        description="Componente compartilhado: Regras de persistência de dados"
    )
    
    prompt_registry.register_prompt(
        name="ethical_guidelines",
        content=ETHICAL_GUIDELINES,
        version="2.0.0",
        author="wedotalent",
        changelog="v2.0 - Diretrizes éticas para avaliação sem viés",
        description="Componente compartilhado: Diretrizes éticas obrigatórias"
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
