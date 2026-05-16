"""
WebSocket de Progresso de Jobs Assíncronos — Fase 5

Endpoint: ws://host/ws/jobs/{job_id}

Emite atualizações em tempo real para tarefas Celery de longa duração.
Mensagens seguem o schema:
  { type, job_id, status, progress, message, result?, error? }
"""
import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.celery_app import celery_app
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)

# Intervalo de polling Celery → WebSocket (segundos)
_POLL_INTERVAL = 1.0
# Timeout máximo para uma sessão WebSocket (segundos) — 3h para entrevistas WSI longas
_MAX_DURATION = 10800


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(websocket: WebSocket, job_id: str, company_id: str = Depends(require_company_id)):
    """
    WebSocket para acompanhar progresso de tarefas Celery em tempo real.

    Conectar: ws://host/ws/jobs/{job_id}

    Mensagens emitidas:
    - status: atualização de status inicial
    - progress: atualização de progresso (0-100%)
    - completed: tarefa concluída com resultado
    - failed: tarefa falhou

    Fechar conexão ao receber 'completed' ou 'failed'.
    """
    await websocket.accept()
    logger.info("WebSocket conectado para job %s", job_id)

    elapsed = 0.0
    last_state = None

    try:
        # Verificar se o job existe
        result = celery_app.AsyncResult(job_id)
        if result.state == "PENDING" and not _job_exists(job_id):
            await websocket.send_text(json.dumps({
                "type": "failed",
                "job_id": job_id,
                "error": "Tarefa não encontrada",
                "timestamp": datetime.utcnow().isoformat(),
            }))
            await websocket.close()
            return

        # Emitir status inicial
        await websocket.send_text(json.dumps({
            "type": "status",
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "Tarefa enfileirada, aguardando execução...",
            "timestamp": datetime.utcnow().isoformat(),
        }))

        while elapsed < _MAX_DURATION:
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

            try:
                result = celery_app.AsyncResult(job_id)
                state = result.state

                if state == last_state and state not in ("SUCCESS", "FAILURE"):
                    continue
                last_state = state

                if state == "STARTED":
                    await websocket.send_text(json.dumps({
                        "type": "progress",
                        "job_id": job_id,
                        "status": "processing",
                        "progress": 5,
                        "message": "Processando...",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))

                elif state == "SUCCESS":
                    payload = result.result if isinstance(result.result, dict) else {}
                    await websocket.send_text(json.dumps({
                        "type": "completed",
                        "job_id": job_id,
                        "status": "completed",
                        "progress": 100,
                        "result": payload,
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
                    break

                elif state == "FAILURE":
                    error_msg = str(result.result) if result.result else "Erro desconhecido"
                    await websocket.send_text(json.dumps({
                        "type": "failed",
                        "job_id": job_id,
                        "status": "failed",
                        "error": error_msg,
                        "retrying": False,
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
                    break

                elif state == "RETRY":
                    await websocket.send_text(json.dumps({
                        "type": "failed",
                        "job_id": job_id,
                        "status": "processing",
                        "error": "Tentando novamente após falha...",
                        "retrying": True,
                        "timestamp": datetime.utcnow().isoformat(),
                    }))

            except Exception as poll_exc:
                logger.warning("Erro ao consultar Celery para job %s: %s", job_id, poll_exc)
                continue

        if elapsed >= _MAX_DURATION:
            await websocket.send_text(json.dumps({
                "type": "failed",
                "job_id": job_id,
                "error": "Timeout: tarefa excedeu o tempo máximo de espera",
                "timestamp": datetime.utcnow().isoformat(),
            }))

    except WebSocketDisconnect:
        logger.info("WebSocket desconectado para job %s após %.0fs", job_id, elapsed)
    except Exception as exc:
        logger.error("Erro no WebSocket para job %s: %s", job_id, exc)
        try:
            await websocket.send_text(json.dumps({
                "type": "failed",
                "job_id": job_id,
                "error": "Erro interno no servidor",
                "timestamp": datetime.utcnow().isoformat(),
            }))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


def _job_exists(job_id: str) -> bool:
    """Heurística: verifica se um job_id parece válido (UUID format)."""
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, job_id, re.IGNORECASE))
