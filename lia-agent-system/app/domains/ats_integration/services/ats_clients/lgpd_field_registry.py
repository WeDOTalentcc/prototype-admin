"""
LGPD Field Registry — ATS clients

Registro centralizado de campos sensíveis por ATS.
Ponto único de atualização quando schemas de ATS mudam.

LGPD Art. 5 (dado pessoal) + Art. 6 (finalidade) + Art. 46 (segurança).
"""

# Campos que requerem consentimento explícito (data_sharing) antes de enviar ao ATS
# Chave: nome do campo no payload WeDOTalent (normalizado)
OUTBOUND_SENSITIVE_FIELDS: frozenset[str] = frozenset({
    "phone",               # Telefone — dado pessoal direto
    "email",               # E-mail — dado pessoal direto
    "salary_expectation",  # Pretensão salarial — dado financeiro sensível
    "wsi_score",           # Score de triagem — dado de avaliação (LGPD Art. 5 XII)
    "cpf",                 # CPF — dado pessoal direto
    "birth_date",          # Data de nascimento
    "disability_info",     # Informação de PCD — dado sensível (LGPD Art. 11)
})

# Mapeamento ATS → campos de texto livre inbound que podem conter PII
# Esses campos recebem strip_pii ao ser importados
INBOUND_TEXT_FIELDS: dict[str, frozenset[str]] = {
    "gupy": frozenset({"observacoes", "notes", "descricao_curriculo"}),
    "pandape": frozenset({"parecer_rh", "observacoes", "notes", "descricao"}),
    "merge": frozenset({"notes", "feedback", "description", "summary"}),
}

# Campos do payload WeDOTalent → campo ATS-específico (para log de auditoria)
GUPY_FIELD_MAP: dict[str, str] = {
    "name": "nome",
    "email": "email",
    "phone": "telefone",
    "linkedin_url": "linkedin",
    "location": "cidade",
    "job_id": "vaga_id",
    "status": "fase",
    "stage": "etapa",
    "notes": "observacoes",
    "rejection_reason": "motivo_reprovacao",
    "salary_expectation": "pretensao_salarial",
    "wsi_score": "nota_avaliacao",
}

PANDAPE_FIELD_MAP: dict[str, str] = {
    "name": "nome_completo",
    "email": "email_principal",
    "phone": "telefone_celular",
    "linkedin_url": "linkedin_url",
    "location": "cidade",
    "job_id": "vaga_id",
    "status": "situacao",
    "stage": "etapa",
    "notes": "parecer_rh",
    "rejection_reason": "motivo_rejeicao",
    "salary_expectation": "pretensao_salarial",
    "wsi_score": "nota_avaliacao",
}


def get_inbound_text_fields(ats_name: str) -> frozenset[str]:
    """Retorna campos de texto livre para strip de PII ao receber do ATS."""
    return INBOUND_TEXT_FIELDS.get(ats_name.lower(), frozenset())
