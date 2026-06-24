from app.domains.base import ActionType, DomainAction

ACTIONS = [
    DomainAction(
        id="{domain_name}_example",
        name="Example Action",
        description="TODO: describe what this action does",
        type=ActionType.ACTION,
        required_params=["param1"],
        optional_params=["param2"],
        requires_confirmation=False,
        tags=["{domain_name}"],
    ),
]
