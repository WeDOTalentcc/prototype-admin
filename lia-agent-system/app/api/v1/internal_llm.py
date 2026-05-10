from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/internal/llm", tags=["Internal LLM"])

_ALLOWED_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def _require_internal(request: Request) -> None:
    """Reject requests that did not originate from the local host."""
    client_host = request.client.host if request.client else None
    if client_host not in _ALLOWED_HOSTS:
        raise HTTPException(status_code=403, detail="Internal endpoint only")


class GenerateRequest(BaseModel):
    prompt: str
    system: str | None = None
    max_tokens: int = 1024


class GenerateResponse(BaseModel):
    text: str


# multi-tenancy: admin/platform-level (internal_) — role-based access required
@router.post("/generate", response_model=GenerateResponse)
async def generate(body: GenerateRequest, request: Request) -> GenerateResponse:
    """Internal endpoint: generates text via the LLM factory.

    Restricted to requests originating from localhost (e.g. the Next.js server
    running on the same host). External clients will receive 403.
    """
    _require_internal(request)

    from app.shared.providers.llm_factory import get_provider_for_tenant

    container = get_provider_for_tenant()
    text = await container.generate_with_fallback(body.prompt, system=body.system)
    return GenerateResponse(text=text)
