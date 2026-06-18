"""
Tool input guards — validação canônica na fronteira LLM→sistema.

O LLM é tratado como sistema externo: todo input que vem de kwargs de tool call
deve ser validado aqui antes de ser usado em queries/conversões de tipo.
"""
import re
import logging

logger = logging.getLogger(__name__)

_UUID_RE = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
)


def validate_uuid_param(param_name: str, value) -> dict | None:
    """Valida que `value` é um UUID válido.
    
    Retorna None se válido. Retorna dict de erro (pronto para return no tool handler)
    se inválido. Uso:
    
        err = validate_uuid_param("job_id", job_id)
        if err:
            return err
        # ... continua com UUID(job_id)
    """
    if not value:
        return {
            "success": False,
            "needs_clarification": True,
            "message": (
                f"O parâmetro '{param_name}' não foi informado. "
                f"Use o UUID do campo 'id' retornado pelas ferramentas de busca."
            ),
        }
    if not _UUID_RE.match(str(value)):
        logger.warning("tool_guards: %s inválido (não-UUID): %r", param_name, str(value)[:60])
        return {
            "success": False,
            "needs_clarification": True,
            "message": (
                f"O valor '{str(value)[:40]}' não é um ID válido para '{param_name}'. "
                f"Use o UUID do campo 'id' retornado pelas ferramentas de busca "
                f"(ex: list_jobs, search_jobs, list_candidates). "
                f"Nunca use o nome ou título como ID."
            ),
        }
    return None


def validate_uuid_params(**params) -> dict | None:
    """Valida múltiplos UUIDs de uma vez. Retorna o primeiro erro encontrado.
    
    Uso:
        err = validate_uuid_params(job_id=job_id, candidate_id=candidate_id)
        if err:
            return err
    """
    for name, value in params.items():
        err = validate_uuid_param(name, value)
        if err:
            return err
    return None
