"""
TwinInferenceService — evaluates candidates using a Digital Twin's reasoning via RAG few-shot.

Flow:
  1. Receive candidate + job context
  2. Embed the candidate profile
  3. K-NN search in twin_decisions for K=5 most similar past decisions
  4. Build few-shot prompt with approved + rejected examples
  5. LLM generates score + reasoning in the SME's style

Apply to: lia-agent-system/app/services/twin_inference_service.py

Wave C1.1 (2026-05-27): twin/decision raw queries + pgvector inline SQL
migrated to DigitalTwinRepository (ADR-001 canonical).
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TwinEvaluation:
    twin_id: str
    twin_name: str
    score: Optional[int]  # 0-100; None if evaluation failed
    decision: str  # approved, rejected, maybe, evaluation_failed
    reasoning: str  # in first person, SME style
    confidence: float  # 0.0-1.0, based on corpus size and similarity
    supporting_examples: list[dict]  # K similar past decisions
    # REGRA 4 anti-silent-fallback (audit 2026-05-27): expose LLM failure explicitly
    evaluation_failed: bool = False
    failure_reason: Optional[str] = None
    needs_manual_review: bool = False


class TwinInferenceService:

    async def evaluate(
        self,
        twin_id: str,
        candidate_profile: dict,
        job_context: dict,
        company_id: str,
        k: int = 5,
        db=None,
    ) -> TwinEvaluation:
        """
        Evaluate a candidate using the Digital Twin's historical reasoning.

        Args:
            twin_id: UUID of the digital twin
            candidate_profile: {name, role_name, skills, experience, ...}
            job_context: {title, description, requirements, ...}
            company_id: tenant scope (multi-tenancy fail-closed)
            k: number of similar examples to retrieve
            db: database session

        Returns:
            TwinEvaluation with score, decision, reasoning in SME style
        """
        from app.domains.agent_studio.repositories.digital_twin_repository import (
            DigitalTwinRepository,
        )

        repo = DigitalTwinRepository(db)

        # 1. Load twin (tenant-scoped)
        twin = await repo.get_by_id(twin_id=twin_id, company_id=company_id)
        if twin is None:
            raise LookupError(
                f"DigitalTwin twin_id={twin_id} not found for company_id={company_id}"
            )

        # 2. Generate embedding for current candidate
        candidate_text = (
            f"Cargo: {job_context.get('title', '')}\n"
            f"Perfil: {json.dumps(candidate_profile, ensure_ascii=False)[:500]}"
        )
        query_embedding = await self._embed(candidate_text)

        # 3. Retrieve K most similar decisions via pgvector (canonical repo)
        examples = await self._retrieve_similar(
            repo=repo,
            twin_id=twin_id,
            company_id=company_id,
            embedding=query_embedding,
            k=k,
        )

        # 4. Separate approved/rejected for few-shot
        approved_ex = [e for e in examples if e["decision"] == "approved"][:3]
        rejected_ex = [e for e in examples if e["decision"] == "rejected"][:2]

        # 5. Build few-shot prompt
        approved_block = "\n".join(
            f"  - Perfil: {json.dumps(e.get('candidate_snapshot', {}), ensure_ascii=False)[:200]}\n"
            f"    Raciocínio: \"{e['reasoning'][:200]}\""
            for e in approved_ex
        ) or "  (sem exemplos aprovados ainda)"

        rejected_block = "\n".join(
            f"  - Perfil: {json.dumps(e.get('candidate_snapshot', {}), ensure_ascii=False)[:200]}\n"
            f"    Raciocínio: \"{e['reasoning'][:200]}\""
            for e in rejected_ex
        ) or "  (sem exemplos rejeitados ainda)"

        prompt = f"""
Você é {twin.twin_name}, especialista em recrutamento com as seguintes especialidades: {', '.join(twin.specialties or [])}.

Com base no seu histórico de decisões:

PERFIS QUE VOCÊ COSTUMA APROVAR:
{approved_block}

PERFIS QUE VOCÊ COSTUMA REJEITAR:
{rejected_block}

Agora avalie este candidato para a vaga de {job_context.get('title', 'a posição')}:
{json.dumps(candidate_profile, ensure_ascii=False, indent=2)[:800]}

Responda com JSON:
{{
  "score": <0-100>,
  "decision": "approved|rejected|maybe",
  "reasoning": "<seu raciocínio em primeira pessoa, máx 3 frases, no estilo de {twin.twin_name}>"
}}
Responda APENAS com o JSON.
"""

        # 6. LLM inference — REGRA 4 (CLAUDE.md): no silent fallback in critical AI path.
        # If LLM fails, return evaluation with explicit failure flags so the caller
        # (and ultimately the recruiter UI) can surface "needs manual review".
        try:
            # Canonical LLM factory (multi-tenant aware). Replaces broken
            # get_llm import (function never existed in llm_factory.py),
            # which previously caused this branch to *always* hit the
            # except: block below and return evaluation_failed=True.
            from app.shared.providers.llm_factory import create_tracked_llm
            llm = create_tracked_llm(
                temperature=0.3,
                service_name="TwinInferenceService",
                operation="evaluate",
                max_output_tokens=512,
                tenant_id=company_id,
            )
            response = await llm.ainvoke(prompt)
            data = json.loads(response.content)
        except Exception as e:
            logger.error(
                "[TwinInference] LLM evaluation failed",
                exc_info=True,
                extra={"twin_id": str(twin.id), "twin_name": twin.twin_name},
            )
            confidence = self._calculate_confidence(twin.decision_count, examples)
            return TwinEvaluation(
                twin_id=str(twin.id),
                twin_name=twin.twin_name,
                score=None,
                decision="evaluation_failed",
                reasoning=f"Avaliação automática indisponível: {type(e).__name__}",
                confidence=0.0,
                supporting_examples=examples,
                evaluation_failed=True,
                failure_reason=str(e)[:200],
                needs_manual_review=True,
            )

        # 7. Calculate confidence based on corpus size and similarity
        confidence = self._calculate_confidence(twin.decision_count, examples)

        return TwinEvaluation(
            twin_id=str(twin.id),
            twin_name=twin.twin_name,
            score=int(data.get("score", 50)),
            decision=data.get("decision", "maybe"),
            reasoning=data.get("reasoning", ""),
            confidence=confidence,
            supporting_examples=examples,
        )

    async def _retrieve_similar(
        self,
        repo,
        twin_id: str,
        company_id: str,
        embedding: Optional[list[float]],
        k: int,
    ) -> list[dict]:
        """Retrieve K most similar decisions from twin's corpus via canonical repo."""
        if not embedding:
            # No embedding — fallback to most recent decisions
            rows = await repo.get_twin_decisions(
                twin_id=twin_id, company_id=company_id, limit=k
            )
            return [
                {
                    "decision": r.decision,
                    "reasoning": r.reasoning,
                    "candidate_snapshot": r.candidate_snapshot or {},
                    "similarity": 0.5,
                }
                for r in rows
            ]

        # pgvector K-NN search via canonical repo
        return await repo.search_similar_decisions(
            twin_id=twin_id,
            company_id=company_id,
            embedding=embedding,
            k=k,
        )

    async def _embed(self, text: str) -> Optional[list[float]]:
        """Generate embedding using existing infrastructure."""
        try:
            from app.domains.sourcing.services.pgv_analyzer import get_text_embedding
            return await get_text_embedding(text)
        except Exception as e:
            logger.warning("[TwinInference] Embedding failed: %s", e)
            return None

    @staticmethod
    def _calculate_confidence(decision_count: int, examples: list[dict]) -> float:
        """
        Calculate confidence based on corpus size and retrieval quality.
        More decisions + higher similarity = higher confidence.
        """
        # Corpus size factor (0.3-1.0, saturates at 100 decisions)
        corpus_factor = min(decision_count / 100, 1.0) * 0.7 + 0.3

        # Average similarity of retrieved examples
        similarities = [e.get("similarity", 0.5) for e in examples]
        avg_sim = sum(similarities) / max(len(similarities), 1)

        # Combined confidence
        return round(min(corpus_factor * avg_sim * 1.2, 1.0), 2)


twin_inference_service = TwinInferenceService()
