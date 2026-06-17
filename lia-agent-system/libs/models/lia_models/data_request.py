"""
Data Request System Models

Sistema para solicitação de dados/documentos aos candidatos.
Permite coleta de informações como CPF, documentos, dados bancários etc.
com portal público de preenchimento e acompanhamento de status.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum
import secrets


class DataRequestStatus(str, enum.Enum):
    """Status da solicitação de dados"""
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DataFieldType(str, enum.Enum):
    """Tipos de campos disponíveis"""
    TEXT = "text"
    CPF = "cpf"
    CNPJ = "cnpj"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    NUMBER = "number"
    CURRENCY = "currency"
    FILE = "file"
    PHOTO = "photo"
    ADDRESS = "address"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    TEXTAREA = "textarea"


class TriggerType(str, enum.Enum):
    """Tipo de gatilho para solicitação"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    STAGE_ENTRY = "stage_entry"
    STAGE_EXIT = "stage_exit"


from lia_config.database import Base


class DataRequestTemplate(Base):
    """
    Template de solicitação de dados configurável por empresa.
    Define quais campos solicitar em cada etapa do processo.
    """
    __tablename__ = "data_request_templates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    trigger_stage = Column(String(100), nullable=True, index=True)
    trigger_type = Column(SQLEnum(TriggerType), default=TriggerType.MANUAL)
    
    is_blocking = Column(Boolean, default=False)
    
    expiration_days = Column(Integer, default=7)
    
    fields = Column(JSON, default=list)
    
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    def __repr__(self):
        return f"<DataRequestTemplate {self.id} - {self.name}>"


class DataRequestField(Base):
    """
    Definição de um campo individual para solicitação.
    Reutilizável em múltiplos templates.
    """
    __tablename__ = "data_request_fields"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    label_en = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    field_type = Column(SQLEnum(DataFieldType), nullable=False)
    
    is_required = Column(Boolean, default=True)
    
    validation_rules = Column(JSON, default=dict)
    
    options = Column(JSON, default=list)
    
    placeholder = Column(String(255), nullable=True)
    help_text = Column(String(500), nullable=True)
    
    max_file_size_mb = Column(Integer, default=10)
    allowed_file_types = Column(ARRAY(String), default=list)
    
    order = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DataRequestField {self.id} - {self.name}>"


class DataRequest(Base):
    """
    Solicitação de dados enviada a um candidato específico.
    Contém link único com token para acesso ao portal público.
    """
    __tablename__ = "data_requests"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("data_request_templates.id", ondelete="SET NULL"), nullable=True)
    
    token = Column(String(64), unique=True, nullable=False, index=True)
    
    status = Column(SQLEnum(DataRequestStatus), default=DataRequestStatus.PENDING, index=True)
    
    fields_requested = Column(JSON, default=list)
    
    fields_completed = Column(JSON, default=list)
    
    trigger_type = Column(SQLEnum(TriggerType), default=TriggerType.MANUAL)
    trigger_stage = Column(String(100), nullable=True)
    
    is_blocking = Column(Boolean, default=False)
    
    expires_at = Column(DateTime, nullable=False)
    
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_verified = Column(Boolean, default=False)
    otp_attempts = Column(Integer, default=0)
    
    sent_via_email = Column(Boolean, default=False)
    sent_via_whatsapp = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    whatsapp_sent_at = Column(DateTime, nullable=True)
    
    reminder_count = Column(Integer, default=0)
    last_reminder_at = Column(DateTime, nullable=True)
    
    collection_method = Column(String(20), nullable=True)
    whatsapp_conversation_state = Column(JSON, default=dict)
    
    first_accessed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    candidate = relationship("Candidate", backref="data_requests")
    vacancy = relationship("JobVacancy", backref="data_requests")
    template = relationship("DataRequestTemplate", backref="data_requests")
    
    @classmethod
    def generate_token(cls) -> str:
        """Gera token único para acesso ao portal"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def generate_otp(cls) -> str:
        """Gera código OTP de 6 dígitos"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_expired(self) -> bool:
        """Verifica se a solicitação expirou"""
        expires = self.expires_at  # type: ignore
        if expires is None:
            return False
        return datetime.utcnow() > expires
    
    def get_completion_percentage(self) -> float:
        """Calcula percentual de campos preenchidos"""
        fields_req = self.fields_requested  # type: ignore
        fields_comp = self.fields_completed  # type: ignore
        if not fields_req:
            return 0.0
        required_fields = [f for f in fields_req if f.get('is_required', True)]
        if not required_fields:
            return 100.0
        completed_names = {f.get('name') for f in (fields_comp or [])}
        filled = sum(1 for f in required_fields if f.get('name') in completed_names)
        return (filled / len(required_fields)) * 100
    
    def __repr__(self):
        return f"<DataRequest {self.id} - {self.status.value}>"


class DataRequestResponse(Base):
    """
    Resposta individual de um campo preenchido pelo candidato.
    Armazena histórico de alterações para auditoria.
    """
    __tablename__ = "data_request_responses"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    data_request_id = Column(UUID(as_uuid=True), ForeignKey("data_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    field_name = Column(String(100), nullable=False, index=True)
    field_type = Column(SQLEnum(DataFieldType), nullable=False)
    
    value = Column(Text, nullable=True)
    
    file_url = Column(String(1000), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_mime_type = Column(String(100), nullable=True)
    
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, default=list)
    
    submitted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    data_request = relationship("DataRequest", backref="responses")
    
    def __repr__(self):
        return f"<DataRequestResponse {self.id} - {self.field_name}>"


class DataRequestConfig(Base):
    """
    Configuração global de solicitação de dados por empresa.
    Define padrões, branding e comportamento do portal.
    """
    __tablename__ = "data_request_configs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    default_expiration_days = Column(Integer, default=7)
    
    require_otp = Column(Boolean, default=True)
    otp_expiration_minutes = Column(Integer, default=10)
    max_otp_attempts = Column(Integer, default=3)
    
    send_email_notification = Column(Boolean, default=True)
    send_whatsapp_notification = Column(Boolean, default=True)
    
    auto_reminder_enabled = Column(Boolean, default=True)
    reminder_days = Column(ARRAY(Integer), default=[2, 5])
    max_reminders = Column(Integer, default=2)
    
    portal_logo_url = Column(Text, nullable=True)
    portal_primary_color = Column(String(7), default="#000000")
    portal_welcome_message = Column(Text, nullable=True)
    portal_thank_you_message = Column(Text, nullable=True)
    
    privacy_policy_url = Column(String(500), nullable=True)
    terms_url = Column(String(500), nullable=True)
    
    collection_mode = Column(String(50), default="portal_only")  # type: ignore[var-annotated]
    collection_messages = Column(JSON, default=dict)  # type: ignore[var-annotated]
    
    lgpd_require_consent = Column(Boolean, default=True)  # type: ignore[var-annotated]
    lgpd_consent_message = Column(Text, nullable=True)  # type: ignore[var-annotated]
    lgpd_disclaimer_text = Column(Text, nullable=True)  # type: ignore[var-annotated]
    lgpd_data_retention_days = Column(Integer, default=365)  # type: ignore[var-annotated]
    lgpd_allow_data_deletion = Column(Boolean, default=True)  # type: ignore[var-annotated]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DataRequestConfig {self.id} - company {self.company_id}>"


class VacancyDataRequestConfig(Base):
    """
    Configuração de solicitação de dados específica por vaga.
    Permite sobrescrever configurações padrão da empresa.
    """
    __tablename__ = "vacancy_data_request_configs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    use_company_defaults = Column(Boolean, default=True)
    
    custom_template_id = Column(UUID(as_uuid=True), ForeignKey("data_request_templates.id", ondelete="SET NULL"), nullable=True)
    
    stage_configs = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vacancy = relationship("JobVacancy", backref="data_request_config")
    custom_template = relationship("DataRequestTemplate")
    
    def __repr__(self):
        return f"<VacancyDataRequestConfig {self.id} - vacancy {self.vacancy_id}>"


DEFAULT_DATA_FIELDS = [
    {
        "name": "cpf",
        "label": "CPF",
        "label_en": "Tax ID (CPF)",
        "field_type": DataFieldType.CPF,
        "is_required": True,
        "placeholder": "000.000.000-00",
        "help_text": "Informe seu CPF (apenas números)",
        "validation_rules": {"pattern": r"^\d{11}$"}
    },
    {
        "name": "rg",
        "label": "RG",
        "label_en": "ID Card (RG)",
        "field_type": DataFieldType.TEXT,
        "is_required": False,
        "help_text": "Número do documento de identidade"
    },
    {
        "name": "birth_date",
        "label": "Data de Nascimento",
        "label_en": "Birth Date",
        "field_type": DataFieldType.DATE,
        "is_required": True
    },
    {
        "name": "phone",
        "label": "Telefone",
        "label_en": "Phone",
        "field_type": DataFieldType.PHONE,
        "is_required": True,
        "placeholder": "(00) 00000-0000"
    },
    {
        "name": "email",
        "label": "E-mail",
        "label_en": "Email",
        "field_type": DataFieldType.EMAIL,
        "is_required": True
    },
    {
        "name": "address",
        "label": "Endereço Completo",
        "label_en": "Full Address",
        "field_type": DataFieldType.ADDRESS,
        "is_required": False
    },
    {
        "name": "bank_account",
        "label": "Dados Bancários",
        "label_en": "Bank Account",
        "field_type": DataFieldType.TEXT,
        "is_required": False,
        "help_text": "Banco, Agência e Conta"
    },
    {
        "name": "pis_pasep",
        "label": "PIS/PASEP",
        "label_en": "PIS/PASEP",
        "field_type": DataFieldType.TEXT,
        "is_required": False
    },
    {
        "name": "ctps",
        "label": "CTPS (Carteira de Trabalho)",
        "label_en": "Work Card (CTPS)",
        "field_type": DataFieldType.TEXT,
        "is_required": False,
        "help_text": "Número e série da CTPS"
    },
    {
        "name": "photo_3x4",
        "label": "Foto 3x4",
        "label_en": "Photo 3x4",
        "field_type": DataFieldType.PHOTO,
        "is_required": False,
        "max_file_size_mb": 5,
        "allowed_file_types": ["image/jpeg", "image/png"]
    },
    {
        "name": "id_document_front",
        "label": "Documento de Identidade (Frente)",
        "label_en": "ID Document (Front)",
        "field_type": DataFieldType.FILE,
        "is_required": False,
        "max_file_size_mb": 10,
        "allowed_file_types": ["image/jpeg", "image/png", "application/pdf"]
    },
    {
        "name": "id_document_back",
        "label": "Documento de Identidade (Verso)",
        "label_en": "ID Document (Back)",
        "field_type": DataFieldType.FILE,
        "is_required": False,
        "max_file_size_mb": 10,
        "allowed_file_types": ["image/jpeg", "image/png", "application/pdf"]
    },
    {
        "name": "proof_of_address",
        "label": "Comprovante de Endereço",
        "label_en": "Proof of Address",
        "field_type": DataFieldType.FILE,
        "is_required": False,
        "max_file_size_mb": 10,
        "allowed_file_types": ["image/jpeg", "image/png", "application/pdf"],
        "help_text": "Conta de luz, água ou telefone recente"
    },
    {
        "name": "education_certificate",
        "label": "Certificado de Escolaridade",
        "label_en": "Education Certificate",
        "field_type": DataFieldType.FILE,
        "is_required": False,
        "max_file_size_mb": 10,
        "allowed_file_types": ["application/pdf", "image/jpeg", "image/png"]
    },
    {
        "name": "salary_expectation",
        "label": "Pretensão Salarial",
        "label_en": "Salary Expectation",
        "field_type": DataFieldType.CURRENCY,
        "is_required": False,
        "placeholder": "R$ 0,00"
    },
    {
        "name": "availability_date",
        "label": "Data de Disponibilidade",
        "label_en": "Availability Date",
        "field_type": DataFieldType.DATE,
        "is_required": False,
        "help_text": "Quando pode iniciar?"
    },
    {
        "name": "emergency_contact",
        "label": "Contato de Emergência",
        "label_en": "Emergency Contact",
        "field_type": DataFieldType.TEXT,
        "is_required": False,
        "help_text": "Nome e telefone"
    },
    {
        "name": "linkedin_url",
        "label": "LinkedIn",
        "label_en": "LinkedIn URL",
        "field_type": DataFieldType.TEXT,
        "is_required": False,
        "placeholder": "https://linkedin.com/in/seu-perfil"
    },
    {
        "name": "portfolio_url",
        "label": "Portfólio",
        "label_en": "Portfolio URL",
        "field_type": DataFieldType.TEXT,
        "is_required": False
    },
    {
        "name": "shirt_size",
        "label": "Tamanho de Camiseta",
        "label_en": "Shirt Size",
        "field_type": DataFieldType.SELECT,
        "is_required": False,
        "options": ["PP", "P", "M", "G", "GG", "XGG"]
    }
]


DEFAULT_STAGE_FIELD_MAPPINGS = {
    "screening": ["cpf", "birth_date", "phone", "email"],
    "interview_hr": ["address", "linkedin_url"],
    "interview_technical": ["portfolio_url"],
    "offer": ["salary_expectation", "availability_date", "bank_account"],
    "hired": [
        "rg", "pis_pasep", "ctps", "photo_3x4",
        "id_document_front", "id_document_back",
        "proof_of_address", "education_certificate",
        "emergency_contact", "shirt_size"
    ]
}
