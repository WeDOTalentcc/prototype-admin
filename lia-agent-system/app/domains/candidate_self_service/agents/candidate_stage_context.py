"""Human-readable stage context for candidate-facing responses."""

STAGE_LABELS: dict[str, str] = {
    "web_submission": "Inscrição recebida",
    "screening": "Em triagem",
    "interview": "Entrevista",
    "rejected": "Processo encerrado",
    "hired": "Aprovado",
}

STAGE_NEXT_STEPS: dict[str, str] = {
    "web_submission": "Sua inscrição foi recebida. O recrutador iniciará a triagem em breve.",
    "screening": "Seu perfil está sendo analisado pela equipe de recrutamento.",
    "interview": "Você avançou para a fase de entrevistas. Fique atento ao agendamento!",
    "rejected": "Agradecemos sua participação. Continuaremos seu perfil em nosso banco de talentos.",
    "hired": "Parabéns! Você foi selecionado. A equipe de RH entrará em contato.",
}


def get_stage_label(stage_key: str) -> str:
    return STAGE_LABELS.get(stage_key, stage_key.replace("_", " ").title())


def get_next_steps(stage_key: str) -> str:
    return STAGE_NEXT_STEPS.get(stage_key, "Para mais informações, entre em contato com o recrutamento.")
