"""
Compliance Health Check models for tracking compliance requirements and verifications.

This module provides models for:
- Health check items for various compliance frameworks (SOX, SOC2, ISO27001, LGPD, BCB498, EUAI, NYC144)
- History tracking for status changes
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from lia_config.database import Base
import enum
import uuid


class ComplianceFrameworkType(str, enum.Enum):
    """Supported compliance frameworks."""
    SOX = "SOX"
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    LGPD = "LGPD"
    BCB498 = "BCB498"
    EUAI = "EUAI"
    NYC144 = "NYC144"


class HealthCheckStatus(str, enum.Enum):
    """Status options for health check items."""
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    PENDING = "pending"
    NOT_APPLICABLE = "not_applicable"
    NOT_CHECKED = "not_checked"


class ReviewFrequency(str, enum.Enum):
    """Review frequency options."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class Priority(str, enum.Enum):
    """Priority levels for health check items."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceHealthCheckItem(Base):
    """
    Compliance Health Check Item.
    
    Tracks individual compliance requirements across multiple frameworks
    with verification status, evidence, and review scheduling.
    """
    __tablename__ = "compliance_health_check_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    framework = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    req_id = Column(String(50), nullable=False, unique=True, index=True)
    
    requirement = Column(String(500), nullable=False)
    evidence = Column(String(500), nullable=True)
    evidence_details = Column(Text, nullable=True)  # Detailed evidence description
    checklist_items = Column(JSONB, nullable=True, default=[])  # List of sub-items to check
    gap_observation = Column(Text, nullable=True)
    
    status = Column(String(20), nullable=False, default="not_checked")
    
    last_checked_at = Column(DateTime, nullable=True)
    checked_by_id = Column(UUID(as_uuid=True), nullable=True)
    checked_by_name = Column(String(255), nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    review_frequency = Column(String(20), default="monthly")
    
    check_comments = Column(Text, nullable=True)
    
    priority = Column(String(20), default="medium")
    
    reference_url = Column(String(500), nullable=True)
    reference_label = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    history = relationship("ComplianceHealthCheckHistory", back_populates="item", order_by="desc(ComplianceHealthCheckHistory.created_at)")
    
    __table_args__ = (
        Index('idx_health_check_framework_status', 'framework', 'status'),
        Index('idx_health_check_framework_category', 'framework', 'category'),
        Index('idx_health_check_next_review', 'next_review_date'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ComplianceHealthCheckItem {self.req_id} - {self.framework}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "framework": self.framework,
            "category": self.category,
            "req_id": self.req_id,
            "requirement": self.requirement,
            "evidence": self.evidence,
            "evidence_details": self.evidence_details,
            "checklist_items": self.checklist_items or [],
            "gap_observation": self.gap_observation,
            "status": self.status,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "checked_by_id": str(self.checked_by_id) if self.checked_by_id else None,
            "checked_by_name": self.checked_by_name,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "review_frequency": self.review_frequency,
            "check_comments": self.check_comments,
            "priority": self.priority,
            "reference_url": self.reference_url,
            "reference_label": self.reference_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComplianceHealthCheckHistory(Base):
    """
    History of status changes for compliance health check items.
    
    Maintains audit trail of all status modifications with user attribution.
    """
    __tablename__ = "compliance_health_check_history"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("compliance_health_check_items.id", ondelete="CASCADE"), nullable=False, index=True)
    
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    changed_by_id = Column(UUID(as_uuid=True), nullable=True)
    changed_by_name = Column(String(255), nullable=True)
    comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    item = relationship("ComplianceHealthCheckItem", back_populates="history")
    
    def __repr__(self):
        return f"<ComplianceHealthCheckHistory {self.id} - {self.old_status} -> {self.new_status}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "item_id": str(self.item_id),
            "old_status": self.old_status,
            "new_status": self.new_status,
            "changed_by_id": str(self.changed_by_id) if self.changed_by_id else None,
            "changed_by_name": self.changed_by_name,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


DEFAULT_HEALTH_CHECK_ITEMS = [
    {
        "framework": "SOX",
        "category": "ITGCs",
        "req_id": "SOX-ITGC-01",
        "requirement": "Controles de acesso lógico implementados para sistemas financeiros",
        "evidence": "Matriz de acessos, logs de autenticação, políticas de senha",
        "priority": "critical",
        "review_frequency": "monthly",
        "reference_url": "https://www.sec.gov/rules/final/33-8238.htm",
        "reference_label": "SEC Rule 33-8238"
    },
    {
        "framework": "SOX",
        "category": "ITGCs",
        "req_id": "SOX-ITGC-02",
        "requirement": "Segregação de funções (SoD) em processos críticos",
        "evidence": "Matriz SoD, documentação de papéis e responsabilidades",
        "priority": "critical",
        "review_frequency": "quarterly",
        "reference_url": "https://pcaobus.org/oversight/standards/auditing-standards",
        "reference_label": "PCAOB AS 2201"
    },
    {
        "framework": "SOX",
        "category": "ITGCs",
        "req_id": "SOX-ITGC-03",
        "requirement": "Gestão de mudanças em sistemas e infraestrutura",
        "evidence": "Registros de mudanças, aprovações documentadas, testes",
        "priority": "high",
        "review_frequency": "monthly",
        "reference_url": "https://www.isaca.org/resources/cobit",
        "reference_label": "COBIT 2019"
    },
    {
        "framework": "SOX",
        "category": "Controles de Aplicação",
        "req_id": "SOX-APP-01",
        "requirement": "Validação de entrada de dados em sistemas financeiros",
        "evidence": "Logs de validação, regras de negócio documentadas",
        "priority": "high",
        "review_frequency": "quarterly",
        "reference_url": "https://www.coso.org/guidance-on-ic",
        "reference_label": "COSO Framework"
    },
    {
        "framework": "SOC2",
        "category": "CC1 - Ambiente de Controle",
        "req_id": "SOC2-CC1-01",
        "requirement": "Comprometimento com integridade e valores éticos",
        "evidence": "Código de conduta, políticas éticas assinadas",
        "priority": "high",
        "review_frequency": "annual",
        "reference_url": "https://www.aicpa.org/resources/landing/system-and-organization-controls-soc-suite-of-services",
        "reference_label": "AICPA SOC 2 Criteria"
    },
    {
        "framework": "SOC2",
        "category": "CC6 - Controles de Acesso",
        "req_id": "SOC2-CC6-01",
        "requirement": "Autenticação multifator para sistemas críticos",
        "evidence": "Configurações de MFA, logs de autenticação",
        "priority": "critical",
        "review_frequency": "monthly",
        "reference_url": "https://www.aicpa.org/resources/landing/system-and-organization-controls-soc-suite-of-services",
        "reference_label": "AICPA SOC 2 CC6"
    },
    {
        "framework": "SOC2",
        "category": "CC6 - Controles de Acesso",
        "req_id": "SOC2-CC6-02",
        "requirement": "Revisão periódica de acessos de usuários",
        "evidence": "Relatórios de revisão de acessos, aprovações",
        "priority": "high",
        "review_frequency": "quarterly",
        "reference_url": "https://www.aicpa.org/resources/landing/system-and-organization-controls-soc-suite-of-services",
        "reference_label": "AICPA SOC 2 CC6"
    },
    {
        "framework": "SOC2",
        "category": "CC7 - Operações do Sistema",
        "req_id": "SOC2-CC7-01",
        "requirement": "Monitoramento contínuo de segurança",
        "evidence": "Logs de SIEM, alertas configurados, dashboards",
        "priority": "critical",
        "review_frequency": "weekly",
        "reference_url": "https://www.aicpa.org/resources/landing/system-and-organization-controls-soc-suite-of-services",
        "reference_label": "AICPA SOC 2 CC7"
    },
    {
        "framework": "ISO27001",
        "category": "A.5 - Políticas de Segurança",
        "req_id": "ISO27001-A5-01",
        "requirement": "Políticas de segurança da informação documentadas e aprovadas",
        "evidence": "Documento de política, aprovações da diretoria",
        "priority": "high",
        "review_frequency": "annual",
        "reference_url": "https://www.iso.org/standard/27001",
        "reference_label": "ISO/IEC 27001:2022 A.5"
    },
    {
        "framework": "ISO27001",
        "category": "A.9 - Controle de Acesso",
        "req_id": "ISO27001-A9-01",
        "requirement": "Política de controle de acesso definida e implementada",
        "evidence": "Política documentada, configurações de sistemas",
        "priority": "critical",
        "review_frequency": "quarterly",
        "reference_url": "https://www.iso.org/standard/27001",
        "reference_label": "ISO/IEC 27001:2022 A.9"
    },
    {
        "framework": "ISO27001",
        "category": "A.12 - Segurança nas Operações",
        "req_id": "ISO27001-A12-01",
        "requirement": "Proteção contra malware implementada",
        "evidence": "Configurações de antivírus, logs de detecção",
        "priority": "high",
        "review_frequency": "monthly",
        "reference_url": "https://www.iso.org/standard/27001",
        "reference_label": "ISO/IEC 27001:2022 A.12"
    },
    {
        "framework": "LGPD",
        "category": "Direitos do Titular",
        "req_id": "LGPD-D1",
        "requirement": "Canal de atendimento ao titular implementado (Art. 18)",
        "evidence": "Portal do titular, registros de solicitações",
        "priority": "critical",
        "review_frequency": "monthly",
        "reference_url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm#art18",
        "reference_label": "LGPD Art. 18"
    },
    {
        "framework": "LGPD",
        "category": "Direitos do Titular",
        "req_id": "LGPD-D2",
        "requirement": "Processo de eliminação de dados pessoais (Art. 18, VI)",
        "evidence": "Procedimento documentado, logs de exclusão",
        "priority": "critical",
        "review_frequency": "quarterly",
        "reference_url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm#art18",
        "reference_label": "LGPD Art. 18, VI"
    },
    {
        "framework": "LGPD",
        "category": "Base Legal",
        "req_id": "LGPD-BL1",
        "requirement": "Registro de bases legais para tratamento de dados",
        "evidence": "Inventário de dados, bases legais documentadas",
        "priority": "high",
        "review_frequency": "quarterly",
        "reference_url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm#art7",
        "reference_label": "LGPD Art. 7"
    },
    {
        "framework": "LGPD",
        "category": "Consentimento",
        "req_id": "LGPD-C1",
        "requirement": "Gestão de consentimentos implementada (Art. 8)",
        "evidence": "Registros de consentimento, timestamps",
        "priority": "critical",
        "review_frequency": "monthly",
        "reference_url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm#art8",
        "reference_label": "LGPD Art. 8"
    },
    {
        "framework": "BCB498",
        "category": "Seguro Cibernético",
        "req_id": "BCB498-SC1",
        "requirement": "Apólice de seguro cibernético contratada",
        "evidence": "Apólice vigente, coberturas documentadas",
        "priority": "critical",
        "review_frequency": "annual",
        "reference_url": "https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolu%C3%A7%C3%A3o%20CMN&numero=4893",
        "reference_label": "Resolução CMN 4893"
    },
    {
        "framework": "BCB498",
        "category": "Incidentes",
        "req_id": "BCB498-IN1",
        "requirement": "Plano de resposta a incidentes cibernéticos",
        "evidence": "Plano documentado, contatos de emergência, runbooks",
        "priority": "critical",
        "review_frequency": "quarterly",
        "reference_url": "https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolu%C3%A7%C3%A3o%20CMN&numero=4893",
        "reference_label": "Resolução CMN 4893 Art. 6"
    },
    {
        "framework": "BCB498",
        "category": "Fornecedores",
        "req_id": "BCB498-FN1",
        "requirement": "Due diligence de fornecedores de tecnologia",
        "evidence": "Avaliações de risco, contratos com cláusulas de segurança",
        "priority": "high",
        "review_frequency": "annual",
        "reference_url": "https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolu%C3%A7%C3%A3o%20CMN&numero=4893",
        "reference_label": "Resolução CMN 4893 Art. 16"
    },
    {
        "framework": "EUAI",
        "category": "Transparência",
        "req_id": "EUAI-T1",
        "requirement": "Explicabilidade de decisões automatizadas de IA",
        "evidence": "Documentação de modelos, explicações de decisões",
        "priority": "critical",
        "review_frequency": "monthly",
        "reference_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206",
        "reference_label": "EU AI Act Art. 13"
    },
    {
        "framework": "EUAI",
        "category": "Supervisão Humana",
        "req_id": "EUAI-SH1",
        "requirement": "Mecanismo de intervenção humana em decisões de IA",
        "evidence": "Processos de override, logs de intervenção",
        "priority": "critical",
        "review_frequency": "monthly",
        "reference_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206",
        "reference_label": "EU AI Act Art. 14"
    },
    {
        "framework": "EUAI",
        "category": "Avaliação de Risco",
        "req_id": "EUAI-AR1",
        "requirement": "Avaliação de impacto de IA de alto risco",
        "evidence": "Relatório de avaliação, mitigações documentadas",
        "priority": "high",
        "review_frequency": "quarterly",
        "reference_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206",
        "reference_label": "EU AI Act Art. 9"
    },
    {
        "framework": "NYC144",
        "category": "Auditoria de Viés",
        "req_id": "NYC144-BA1",
        "requirement": "Auditoria anual de viés em ferramentas de recrutamento com IA",
        "evidence": "Relatório de auditoria de viés, métricas de impacto",
        "priority": "critical",
        "review_frequency": "annual",
        "reference_url": "https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=4344524&GUID=B051915D-A9AC-451E-81F8-6596032FA3F9",
        "reference_label": "NYC Local Law 144 of 2021"
    },
    {
        "framework": "NYC144",
        "category": "Notificação",
        "req_id": "NYC144-N1",
        "requirement": "Notificação aos candidatos sobre uso de IA",
        "evidence": "Textos de notificação, registros de comunicação",
        "priority": "critical",
        "review_frequency": "monthly",
        "reference_url": "https://rules.cityofnewyork.us/rule/automated-employment-decision-tools/",
        "reference_label": "DCWP AEDT Rules"
    },
    {
        "framework": "NYC144",
        "category": "Publicação",
        "req_id": "NYC144-P1",
        "requirement": "Publicação de resultados de auditoria de viés",
        "evidence": "Relatório publicado no site, data de publicação",
        "priority": "high",
        "review_frequency": "annual",
        "reference_url": "https://rules.cityofnewyork.us/rule/automated-employment-decision-tools/",
        "reference_label": "DCWP AEDT Rules Section 5-301"
    },
]
