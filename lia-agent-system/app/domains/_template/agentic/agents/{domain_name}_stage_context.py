from dataclasses import dataclass, field
from typing import Optional


@dataclass
class {DomainName}StageContext:
    session_id: str = ""
    company_id: str = ""
    current_step: str = "initial"
    metadata: dict = field(default_factory=dict)
