from app.domains.base import DomainAction

WORKFORCE_ACTIONS: list[DomainAction] = [
    DomainAction(name="get_workforce_plan_summary", description="Resumo do planejamento de força de trabalho", requires_confirmation=False),
]
