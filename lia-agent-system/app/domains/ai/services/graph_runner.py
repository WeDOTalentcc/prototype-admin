"""
Graph Runner Service - Manages graph execution with database-backed state persistence.

Provides high-level interface for running LangGraph-style state machines
with session management, state persistence, and streaming support.
"""
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from lia_agents_core.state_machine import JobWizardState, WizardStage, create_initial_state
from sqlalchemy import and_, select, update

from app.core.database import AsyncSessionLocal
# Task #850 — JobWizardGraph was removed. The legacy `lia_assistant_graph`
# endpoints that use this runner are now dead code and will surface a
# clear NotImplementedError if invoked. The canonical job-creation
# pipeline is `app.domains.job_creation.graph.JobCreationGraph`.
JobWizardGraph: Any = None  # type: ignore[assignment]
job_wizard_graph: Any = None
from app.domains.recruiter_assistant.services.memory_service import MemoryService, memory_service
from lia_models.graph_session import GraphSession

logger = logging.getLogger(__name__)


class DatabaseSessionStore:
    """
    Database-backed store for session states.
    
    Provides durable persistence across restarts with:
    - Automatic cleanup of stale sessions
    - Session recovery
    - Multi-tenant isolation
    """
    
    def __init__(self):
        self._cache: dict[str, JobWizardState] = {}
        self._cache_timeout = 300
        self._cache_timestamps: dict[str, datetime] = {}
    
    async def get(self, session_id: str) -> JobWizardState | None:
        """Get state for a session from cache or database."""
        if session_id in self._cache:
            cache_time = self._cache_timestamps.get(session_id)
            if cache_time and (datetime.utcnow() - cache_time).total_seconds() < self._cache_timeout:
                return self._cache[session_id]
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(GraphSession).where(
                    and_(
                        GraphSession.session_id == session_id,
                        GraphSession.is_active
                    )
                )
            )
            session = result.scalar_one_or_none()
            
            if session:
                state = session.to_state()
                self._cache[session_id] = state
                self._cache_timestamps[session_id] = datetime.utcnow()
                return state
            
            return None
    
    async def set(self, session_id: str, state: JobWizardState) -> None:
        """Store state for a session in database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(GraphSession).where(GraphSession.session_id == session_id)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.update_from_state(state)
                existing.last_activity_at = datetime.utcnow()
            else:
                new_session = GraphSession.from_state(state, session_id)
                db.add(new_session)
            
            await db.commit()
        
        self._cache[session_id] = state
        self._cache_timestamps[session_id] = datetime.utcnow()
    
    async def delete(self, session_id: str) -> None:
        """Soft-delete session (mark as inactive)."""
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(GraphSession)
                .where(GraphSession.session_id == session_id)
                .values(is_active=False)
            )
            await db.commit()
        
        if session_id in self._cache:
            del self._cache[session_id]
        if session_id in self._cache_timestamps:
            del self._cache_timestamps[session_id]
    
    async def list_sessions(self, company_id: str | None = None, limit: int = 100) -> list[str]:
        """List all active sessions, optionally filtered by company."""
        async with AsyncSessionLocal() as db:
            query = select(GraphSession.session_id).where(GraphSession.is_active)
            
            if company_id:
                query = query.where(GraphSession.company_id == UUID(company_id))
            
            query = query.order_by(GraphSession.last_activity_at.desc()).limit(limit)
            
            result = await db.execute(query)
            return [row[0] for row in result.all()]
    
    async def cleanup_stale_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions inactive for more than max_age_hours."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(GraphSession)
                .where(
                    and_(
                        GraphSession.last_activity_at < cutoff,
                        GraphSession.is_active,
                        not GraphSession.is_complete
                    )
                )
                .values(is_active=False)
            )
            await db.commit()
            return result.rowcount or 0


class GraphRunnerService:
    """
    Service to manage graph execution with database persistence.
    
    Provides:
    - Session state management with database backing
    - Graph execution with state persistence
    - Streaming execution for real-time updates
    - Integration with memory service for conversation storage
    - Session recovery after restarts
    """
    
    def __init__(
        self,
        graph: "Any | None" = None,
        memory: MemoryService | None = None
    ):
        # Task #850: `job_wizard_graph` is intentionally `None` at module
        # scope — the legacy graph was deleted. When `graph` is not
        # supplied, `run_job_wizard()` reroutes to the canonical
        # `JobCreationGraph` instead of operating on the legacy graph.
        self.graph = graph if graph is not None else job_wizard_graph
        self.memory = memory or memory_service
        self.state_store = DatabaseSessionStore()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    def _summarize_stage(stage: str, intake_payload: dict[str, Any]) -> str:
        """Build a recruiter-facing message when the canonical graph
        node didn't emit one explicitly. Used by the legacy
        `run_job_wizard` reroute so REST callers always see a
        non-empty `response_text`.
        """
        title = ((intake_payload or {}).get("title") or {}).get("value") or ""
        seniority = ((intake_payload or {}).get("seniority") or {}).get("value") or ""
        head = (title + (f" ({seniority})" if seniority else "")).strip()
        if stage == "intake":
            if head:
                return f"Captei a vaga: {head}. Vou seguir para o próximo passo."
            return "Captei o pedido inicial. Pode me dar mais detalhes da vaga?"
        if stage == "jd_enrichment":
            return "Enriqueci a descrição da vaga — preciso da sua aprovação."
        if stage == "wsi_questions":
            return "Sugeri perguntas de triagem WSI — preciso da sua aprovação."
        return f"Etapa atual: {stage}."

    async def run_job_wizard(
        self,
        session_id: str,
        user_message: str,
        company_id: str,
        user_id: str,
        existing_draft: dict[str, Any] | None = None,
        current_stage: str | None = None
    ) -> dict[str, Any]:
        """
        Run the job wizard graph for a user message.
        
        Loads existing session state from database if available, otherwise creates
        a new state. Executes the graph and persists the result.
        
        Args:
            session_id: Unique session identifier
            user_message: User's input message
            company_id: Company ID for multi-tenancy
            user_id: User making the request
            existing_draft: Optional existing job draft data
            current_stage: Optional current stage to resume from
            
        Returns:
            Dict with execution results including:
            - response_text: LIA's response
            - job_draft: Current job draft state
            - current_stage: Current wizard stage
            - reasoning_steps: List of reasoning steps taken
            - execution_id: Unique ID for this execution
        """
        # Task #850: legacy JobWizardGraph was retired. This entry point
        # is the supported compatibility shim — REST routes
        # (`/lia-assistant/job-wizard/graph-orchestrate`) call it and we
        # forward to the canonical `JobCreationGraph`, then translate
        # the canonical state back into the legacy
        # `GraphOrchestratorResponse` shape.
        if self.graph is None:
            from app.domains.job_creation.graph import job_creation_graph
            from app.domains.job_creation.services.intake_extractor import (
                get_intake_extractor,
            )

            self.logger.info(
                "[GraphRunnerService] Routing run_job_wizard to "
                "JobCreationGraph (Task #850 canonical) | session=%s",
                session_id,
            )
            payload = get_intake_extractor().extract(user_message)
            initial_state: dict[str, Any] = {
                "company_id": company_id,
                "user_id": user_id,
                "session_id": session_id,
                "raw_input": user_message,
                "query": user_message,
                "intake_payload": payload.model_dump(),
                "messages": [{"role": "user", "content": user_message}],
                "current_stage": current_stage or "intake",
                "draft": existing_draft or {},
            }
            # `JobCreationGraph.invoke(state, thread_id)` — state is
            # the first positional, the thread_id (session_id) is the
            # second. Reversing these silently corrupts checkpointing.
            result = job_creation_graph.invoke(initial_state, session_id)

            # Translate canonical state → legacy GraphOrchestratorResponse.
            # Canonical keys we map from:
            #   - intake_payload  : dict shape of JobIntakePayload (the draft)
            #   - ws_stage_payload: per-stage UI payload {type, stage, data}
            #   - current_stage   : the stage we landed on
            #   - stage_history   : list of stages traversed → reasoning trace
            stage_payload = result.get("ws_stage_payload") or {}
            stage_data = stage_payload.get("data") or {}
            response_text = (
                stage_data.get("message")
                or stage_data.get("response_text")
                or self._summarize_stage(
                    result.get("current_stage", "intake"),
                    result.get("intake_payload") or {},
                )
            )
            job_draft = (
                result.get("intake_payload")
                or stage_data.get("intake_payload")
                or existing_draft
                or {}
            )
            reasoning_steps = [
                f"stage:{s}" for s in (result.get("stage_history") or [])
            ]
            return {
                "response_text": response_text,
                "job_draft": job_draft,
                "current_stage": result.get("current_stage", "intake"),
                "reasoning_steps": reasoning_steps,
                "execution_id": session_id,
            }

        self.logger.info(f"Running job wizard for session {session_id}")
        
        existing_state = await self.state_store.get(session_id)
        
        if existing_state:
            existing_state["messages"].append({
                "role": "user",
                "content": user_message
            })
            
            existing_state["reasoning_steps"] = []
            existing_state["tool_calls"] = []
            existing_state["tool_results"] = []
            existing_state["error"] = None
            existing_state["response_text"] = None
            existing_state["extracted_fields"] = {}
            existing_state["should_continue"] = True
            
            if existing_draft:
                existing_state["job_draft"].update(existing_draft)
            if current_stage:
                existing_state["current_stage"] = current_stage
            
            state = existing_state
        else:
            draft = existing_draft or {}
            stage = current_stage or WizardStage.INITIAL.value
            
            state = create_initial_state(
                session_id=session_id,
                company_id=company_id,
                user_id=user_id,
                user_message=user_message,
                existing_draft=draft,
                current_stage=stage
            )
        
        try:
            await self.memory.store_message(
                session_id=session_id,
                role="user",
                content=user_message,
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                user_id=user_id,
                metadata={
                    "stage": state["current_stage"],
                    "source": "job_wizard"
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to store user message in memory: {e}")
        
        final_state = await self.graph.invoke(state)
        
        await self.state_store.set(session_id, final_state)
        
        if final_state.get("response_text"):
            try:
                await self.memory.store_message(
                    session_id=session_id,
                    role="assistant",
                    content=final_state["response_text"],
                    company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                    user_id=user_id,
                    metadata={
                        "stage": final_state["current_stage"],
                        "source": "job_wizard",
                        "reasoning_steps": final_state.get("reasoning_steps", [])
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to store assistant message in memory: {e}")
        
        execution_id = str(uuid4())
        
        return {
            "execution_id": execution_id,
            "session_id": session_id,
            "response_text": final_state.get("response_text", ""),
            "job_draft": final_state.get("job_draft", {}),
            "current_stage": final_state.get("current_stage", WizardStage.INITIAL.value),
            "confidence_scores": final_state.get("confidence_scores", {}),
            "reasoning_steps": final_state.get("reasoning_steps", []),
            "extracted_fields": final_state.get("extracted_fields", {}),
            "error": final_state.get("error"),
            "intent": final_state.get("intent"),
            "is_complete": final_state.get("current_stage") == WizardStage.COMPLETE.value
        }
    
    async def stream_job_wizard(
        self,
        session_id: str,
        user_message: str,
        company_id: str,
        user_id: str,
        existing_draft: dict[str, Any] | None = None,
        current_stage: str | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream job wizard execution for real-time updates.

        Task #850: this method targeted the legacy `JobWizardGraph` which
        is now retired. The canonical `JobCreationGraph` does not
        currently expose a streaming interface — recruiter UI streaming
        is handled via the WS layer (`agent_chat_ws`) directly. There
        are no in-tree callers (verified by grep). To prevent silent
        failure if a future caller is wired up, we fail loudly with a
        clear migration message instead of dispatching to the removed
        legacy graph.
        """
        if self.graph is None:
            raise NotImplementedError(
                "stream_job_wizard() targeted the retired legacy "
                "JobWizardGraph (Task #850). The canonical "
                "JobCreationGraph does not expose a streaming interface; "
                "use the WS layer (agent_chat_ws) for recruiter UI "
                "streaming or call run_job_wizard() for a unary response."
            )
        self.logger.info(f"Streaming job wizard for session {session_id}")

        existing_state = await self.state_store.get(session_id)
        
        if existing_state:
            existing_state["messages"].append({
                "role": "user",
                "content": user_message
            })
            existing_state["reasoning_steps"] = []
            existing_state["tool_calls"] = []
            existing_state["tool_results"] = []
            existing_state["error"] = None
            existing_state["should_continue"] = True
            
            if existing_draft:
                existing_state["job_draft"].update(existing_draft)
            if current_stage:
                existing_state["current_stage"] = current_stage
            
            state = existing_state
        else:
            draft = existing_draft or {}
            stage = current_stage or WizardStage.INITIAL.value
            
            state = create_initial_state(
                session_id=session_id,
                company_id=company_id,
                user_id=user_id,
                user_message=user_message,
                existing_draft=draft,
                current_stage=stage
            )
        
        async for update in self.graph.stream(state):
            yield update
            
            if update.get("type") == "complete":
                final_state = update.get("final_state", {})
                
                state["current_stage"] = final_state.get("current_stage", state["current_stage"])
                state["job_draft"] = final_state.get("job_draft", state["job_draft"])
                state["response_text"] = final_state.get("response_text")
                state["reasoning_steps"] = final_state.get("reasoning_steps", [])
                state["error"] = final_state.get("error")
                
                await self.state_store.set(session_id, state)
    
    async def get_session_state(self, session_id: str) -> dict[str, Any] | None:
        """
        Get current state for a session from database.
        
        Returns:
            Session state dict or None if session doesn't exist
        """
        state = await self.state_store.get(session_id)
        if not state:
            return None
        
        return {
            "session_id": session_id,
            "current_stage": state.get("current_stage"),
            "job_draft": state.get("job_draft", {}),
            "confidence_scores": state.get("confidence_scores", {}),
            "messages": state.get("messages", []),
            "last_response": state.get("response_text"),
            "is_complete": state.get("current_stage") == WizardStage.COMPLETE.value
        }
    
    async def reset_session(self, session_id: str) -> bool:
        """
        Reset session state.
        
        Marks session as inactive and clears memory.
        
        Returns:
            True if session existed and was reset, False otherwise
        """
        state = await self.state_store.get(session_id)
        if state:
            try:
                company_id = state.get("company_id")
                if company_id:
                    await self.memory.delete_session_memory(
                        session_id=session_id,
                        company_id=UUID(company_id) if isinstance(company_id, str) else company_id
                    )
            except Exception as e:
                self.logger.warning(f"Failed to delete memory for session {session_id}: {e}")
            
            await self.state_store.delete(session_id)
            self.logger.info(f"Reset session: {session_id}")
            return True
        
        return False
    
    async def get_session_history(
        self,
        session_id: str,
        company_id: str,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get conversation history for a session from memory.
        
        Returns:
            List of messages in chronological order
        """
        try:
            messages = await self.memory.get_conversation_context(
                session_id=session_id,
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                limit=limit
            )
            return messages
        except Exception as e:
            self.logger.error(f"Failed to get session history: {e}")
            return []
    
    async def list_active_sessions(self, company_id: str | None = None) -> list[str]:
        """Get list of all active session IDs."""
        return await self.state_store.list_sessions(company_id)
    
    async def cleanup_stale_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions that have been inactive for too long."""
        count = await self.state_store.cleanup_stale_sessions(max_age_hours)
        self.logger.info(f"Cleaned up {count} stale sessions")
        return count
    
    def get_graph_info(self) -> dict[str, Any]:
        """Get information about the graph structure."""
        return self.graph.get_graph_structure()


graph_runner_service = GraphRunnerService()
