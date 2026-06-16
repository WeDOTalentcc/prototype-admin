"""
Centralized parameter validation for domain tools.

Provides a @validate_params decorator that validates tool parameters
using Pydantic schemas before execution, ensuring consistent validation
across all domains.

Usage:
    from pydantic import BaseModel
    
    class MoveCandiateParams(BaseModel):
        vacancy_candidate_id: str
        to_stage: str
        from_stage: Optional[str] = None
    
    @validate_params(MoveCandiateParams)
    async def handle_move_candidate(params, context):
        # params is now validated and typed
        ...
"""
import functools
import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ParamValidationError(Exception):
    def __init__(self, action_id: str, errors: list):
        self.action_id = action_id
        self.errors = errors
        details = "; ".join(
            f"{e.get('loc', ['?'])[0]}: {e.get('msg', 'invalid')}"
            for e in errors
        )
        super().__init__(f"Validation failed for '{action_id}': {details}")


def validate_params(schema: type[BaseModel], action_id: str = ""):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(params: dict[str, Any], context: dict[str, Any] | None = None, **kwargs):
            aid = action_id or func.__name__
            try:
                validated = schema(**params)
                validated_dict = validated.model_dump()
                return await func(validated_dict, context, **kwargs)
            except ValidationError as e:
                errors = e.errors(include_url=False)
                logger.warning(
                    f"[PARAM-VALIDATION] {aid}: {len(errors)} validation errors. "
                    f"Params keys: {list(params.keys())}"
                )
                return {
                    "success": False,
                    "error": f"Parâmetros inválidos para '{aid}'",
                    "validation_errors": [
                        {
                            "field": ".".join(str(x) for x in err.get("loc", [])),
                            "message": err.get("msg", ""),
                            "type": err.get("type", ""),
                        }
                        for err in errors
                    ],
                }
        return wrapper
    return decorator


class ToolParamSchemas:
    """Common parameter schemas for reuse across domains."""

    class CandidateId(BaseModel):
        candidate_id: str

    class VacancyCandidateId(BaseModel):
        vacancy_candidate_id: str

    class CompanyId(BaseModel):
        company_id: str

    class SearchQuery(BaseModel):
        query: str
        limit: int = 20
        offset: int = 0

    class MoveCandidate(BaseModel):
        vacancy_candidate_id: str
        to_stage: str
        from_stage: str | None = None
        sub_status: str | None = None
        prompt: str | None = None
        channel: str | None = None

    class PredictSubStatus(BaseModel):
        vacancy_candidate_id: str
        from_stage: str
        to_stage: str
