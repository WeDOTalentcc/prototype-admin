"""CredentialsAccessLog model — LGPD Art. 37 audit trail for credentials decryption.

Wave 3 Camada 3 — registered 2026-05-22
=======================================

LGPD Art. 37 (Records of Processing Activities — "Registro das Operacoes
de Tratamento") recomenda registro de TODO acesso a dados pessoais
sensiveis. Credenciais de integracoes (API keys de Greenhouse/Workday/HRIS,
OAuth tokens, webhook secrets) sao secret material que da acesso indireto
a dados pessoais de candidatos terceiros — qualquer decryption precisa
deixar trilha auditavel.

Pattern:
--------
Toda chamada a ``IntegrationsHubRepository.get_decrypted_credentials``
escreve uma linha aqui ANTES do decrypt acontecer. Se o decrypt falhar,
a entrada ainda persiste — indicando attempt (intent audit).

Campos:
-------
- ``company_id``: tenant owner (multi-tenancy)
- ``integration_connection_id``: conexao especifica (nullable se acesso
  generico ainda nao resolvido)
- ``accessed_at``: timestamp UTC do attempt
- ``accessor_user_id``: usuario humano (FK users) quando aplicavel
- ``accessor_type``: ``human_user`` | ``system`` | ``agent`` |
  ``celery_task`` (categoria do consumer)
- ``access_purpose``: motivo curto, e.g. ``webhook_dispatch``,
  ``sync_check``, ``manual_test``, ``health_check`` (REQUIRED — sensor
  forca caller a documentar)
- ``client_ip``: best-effort IP (FastAPI request.client.host quando
  middleware popula; null em path Celery/system)
- ``request_id``: X-Request-ID quando dentro de request HTTP (corr
  forensics com request_envelope)

Indexes:
--------
- ``(company_id, accessed_at)``: forensic query por janela temporal
  filtrada por tenant
- ``(integration_connection_id)``: rastrear todos os acessos a uma
  conexao especifica (resposta a vazamento)
- ``(request_id)``: corr cross-system com audit_log / request_envelope
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from lia_config.database import Base


class CredentialsAccessLog(Base):
    """LGPD Art. 37 audit trail — every IntegrationConnection credentials decrypt.

    Append-only (no UPDATE/DELETE in normal flow). Retention policy: TBD
    (suggested 2 years — covers most regulatory windows + breach forensics).
    """

    __tablename__ = "credentials_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("company_profiles.id"),
        nullable=False,
        index=True,
    )

    integration_connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("integration_connections.id"),
        nullable=True,
        index=True,
    )

    accessed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Accessor identity (audit forensics)
    accessor_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    accessor_type = Column(String(50), nullable=False)
    # 'human_user' | 'system' | 'agent' | 'celery_task'

    access_purpose = Column(String(200), nullable=False)
    # e.g. 'webhook_dispatch', 'sync_check', 'manual_test', 'health_check'

    client_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    request_id = Column(String(100), nullable=True, index=True)

    __table_args__ = (
        Index(
            "ix_credentials_access_company_time",
            "company_id",
            "accessed_at",
        ),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<CredentialsAccessLog id={self.id} company={self.company_id} "
            f"purpose={self.access_purpose} type={self.accessor_type}>"
        )
