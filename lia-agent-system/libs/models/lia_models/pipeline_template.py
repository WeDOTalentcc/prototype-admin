"""
Pipeline Template models for reusable recruitment process stage templates.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class PipelineTemplate(Base):
    """
    Represents a reusable pipeline template for job creation.
    Templates define the stages of a recruitment process that can be applied to job vacancies.
    """
    __tablename__ = "pipeline_templates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    stages = Column(JSON, default=list)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Pipeline Templates Sprint 2026-05-26 — auto-suggest hints + is_archived (migration 208)
    department_hint = Column(JSON, nullable=True)
    seniority_hint = Column(JSON, nullable=True)
    job_family_hint = Column(JSON, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False, server_default="false")
    # Fase A Opção 2 (2026-06-01): configuração de saturação opcional
    # Capturada no 'Salvar como template' quando o recrutador inclui.
    # Shape: {threshold_web, threshold_sourcing, unlock_increment, unlock_hours}
    saturation_config = Column(JSONB, nullable=True, default=None)
    updated_by = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<PipelineTemplate {self.id} - {self.name}>"


DEFAULT_PIPELINE_TEMPLATES = [
    {
        "name": "Tech Standard",
        "description": "Processo padrão para vagas de tecnologia com 5 etapas estruturadas",
        "stages": [
            {
                "name": "Triagem CV",
                "order": 1,
                "type": "automatic",
                "sla_days": 2,
                "instructions": "Análise automática de CV pela LIA com base nos requisitos da vaga"
            },
            {
                "name": "Entrevista Técnica",
                "order": 2,
                "type": "hybrid",
                "sla_days": 5,
                "instructions": "Avaliação técnica com líder técnico ou arquiteto"
            },
            {
                "name": "Entrevista RH",
                "order": 3,
                "type": "manual",
                "sla_days": 3,
                "instructions": "Avaliação cultural e comportamental com equipe de RH"
            },
            {
                "name": "Entrevista Final",
                "order": 4,
                "type": "manual",
                "sla_days": 5,
                "instructions": "Entrevista final com gestor da área"
            },
            {
                "name": "Proposta",
                "order": 5,
                "type": "manual",
                "sla_days": 3,
                "instructions": "Elaboração e apresentação de proposta ao candidato"
            }
        ],
        "is_default": True
    },
    {
        "name": "Fast Track",
        "description": "Processo acelerado para contratações urgentes com 3 etapas",
        "stages": [
            {
                "name": "Triagem + Técnico",
                "order": 1,
                "type": "automatic",
                "sla_days": 3,
                "instructions": "Triagem automática combinada com avaliação técnica básica"
            },
            {
                "name": "Entrevista Única",
                "order": 2,
                "type": "manual",
                "sla_days": 5,
                "instructions": "Entrevista consolidada com gestor e RH juntos"
            },
            {
                "name": "Proposta",
                "order": 3,
                "type": "manual",
                "sla_days": 2,
                "instructions": "Proposta rápida para fechamento ágil"
            }
        ],
        "is_default": False
    },
    {
        "name": "Executive",
        "description": "Processo completo para posições executivas e de liderança com 6 etapas",
        "stages": [
            {
                "name": "Assessment Comportamental",
                "order": 1,
                "type": "automatic",
                "sla_days": 5,
                "instructions": "Aplicação de testes comportamentais e psicométricos"
            },
            {
                "name": "Entrevista RH",
                "order": 2,
                "type": "manual",
                "sla_days": 5,
                "instructions": "Entrevista aprofundada com foco em liderança e cultura"
            },
            {
                "name": "Entrevista Técnica",
                "order": 3,
                "type": "manual",
                "sla_days": 7,
                "instructions": "Avaliação de competências técnicas e estratégicas"
            },
            {
                "name": "Painel de Gestores",
                "order": 4,
                "type": "manual",
                "sla_days": 7,
                "instructions": "Apresentação e avaliação por comitê de diretores"
            },
            {
                "name": "Referências",
                "order": 5,
                "type": "manual",
                "sla_days": 5,
                "instructions": "Checagem de referências profissionais"
            },
            {
                "name": "Proposta",
                "order": 6,
                "type": "manual",
                "sla_days": 5,
                "instructions": "Elaboração de pacote de remuneração executivo"
            }
        ],
        "is_default": False
    },
    {
        "name": "Estágio/Trainee",
        "description": "Processo simplificado para programas de estágio e trainee",
        "stages": [
            {
                "name": "Triagem Inicial",
                "order": 1,
                "type": "automatic",
                "sla_days": 2,
                "instructions": "Verificação de requisitos básicos e formação acadêmica"
            },
            {
                "name": "Dinâmica de Grupo",
                "order": 2,
                "type": "manual",
                "sla_days": 5,
                "instructions": "Avaliação em grupo com cases práticos"
            },
            {
                "name": "Entrevista Final",
                "order": 3,
                "type": "manual",
                "sla_days": 3,
                "instructions": "Entrevista individual com gestor"
            },
            {
                "name": "Proposta",
                "order": 4,
                "type": "manual",
                "sla_days": 2,
                "instructions": "Apresentação do programa e condições"
            }
        ],
        "is_default": False
    },
    {
        "name": "Operacional",
        "description": "Processo otimizado para vagas operacionais de alto volume",
        "stages": [
            {
                "name": "Triagem Automática",
                "order": 1,
                "type": "automatic",
                "sla_days": 1,
                "instructions": "Verificação rápida de requisitos mínimos"
            },
            {
                "name": "Entrevista Presencial",
                "order": 2,
                "type": "manual",
                "sla_days": 3,
                "instructions": "Entrevista breve com supervisor"
            },
            {
                "name": "Contratação",
                "order": 3,
                "type": "manual",
                "sla_days": 2,
                "instructions": "Formalização e documentação"
            }
        ],
        "is_default": False
    }
]
