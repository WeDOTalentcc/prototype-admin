"""
ARQUIVO NOVO: libs/models/lia_models/retention_policy.py

Modelo de política de retenção de dados por empresa (LGPD Art. 15-16).

COMO APLICAR:
  1. Copiar este arquivo para libs/models/lia_models/retention_policy.py
  2. Adicionar import em libs/models/lia_models/__init__.py:
     from .retention_policy import CompanyRetentionPolicy
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from lia_config.database import Base


class CompanyRetentionPolicy(Base):
    """
    Política de retenção de dados por empresa.

    Por default: auto_anonymize=False (opt-in).
    A anonimização só roda quando o cliente ativa explicitamente.

    Compliance:
      - LGPD Art. 15: dados pessoais devem ser eliminados após a finalidade
      - LGPD Art. 16: exceções para obrigações legais (recomendamos 24 meses)
      - EU GDPR Art. 5(1)(e): storage limitation principle
    """

    __tablename__ = "company_retention_policies"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # Quantos meses manter dados de candidatos não contratados
    # Default: 24 meses (2 anos) — alinhado com prática de mercado RH
    retention_months: Mapped[int] = mapped_column(Integer, default=24, nullable=False)

    # OFF por default — empresa precisa ativar explicitamente (opt-in)
    auto_anonymize: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Auditoria de ativação (quem ligou o switch)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    activated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Última execução do job de limpeza para esta empresa
    last_cleanup_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_cleanup_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyRetentionPolicy company={self.company_id} "
            f"months={self.retention_months} auto={self.auto_anonymize}>"
        )
