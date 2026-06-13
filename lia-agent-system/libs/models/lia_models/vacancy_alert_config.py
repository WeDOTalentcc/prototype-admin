"""
VacancyAlertConfig — configuração de alertas por vaga + recrutador.
Sobrescreve a frequência global do recrutador para uma vaga específica.
"""
import uuid
from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from lia_config.database import Base


class VacancyAlertConfig(Base):
    __tablename__ = "vacancy_alert_configs"
    __table_args__ = (
        UniqueConstraint("vacancy_id", "recruiter_id", "alert_type", name="uq_vacancy_alert"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String, nullable=False, index=True)  # multi-tenancy
    vacancy_id = Column(String, nullable=False, index=True)
    recruiter_id = Column(String, nullable=False, index=True)
    alert_type = Column(String(100), nullable=False)
    # Valores: daily | twice_daily | weekly | monthly | off
    frequency = Column(String(20), nullable=False, default="daily")
