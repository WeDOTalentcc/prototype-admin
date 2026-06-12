"""
Post-completion actions: feedback generation, notifications, WSI persistence.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.triagem import TriagemMessage, TriagemSession

from app.domains.recruitment.repositories.triagem_session_repository import (
    find_job_vacancy_for_triagem,
)

from ._shared import _get_event_dispatcher, _get_screening_config
from .wsi_blocks import _resolve_screening_mode

logger = logging.getLogger(__name__)


async def _trigger_post_completion(db: AsyncSession, session: TriagemSession, response_scores: list[dict[str, Any]] = None) -> dict[str, Any]:
    actions = {
        "email_confirmation": "queued",
        "recruiter_notification": "queued",
        "pipeline_update": "queued",
        "wsi_persistence": "queued",
        "audit_log": "created",
    }

    logger.info(
        f"[Triagem] Post-completion triggered for session {session.token}: "
        f"candidate={session.candidate_name}, job={session.job_title}, "
        f"score={session.wsi_final_score}, recommendation={session.recommendation}"
    )

    try:
        import json as _json
        import os as _os

        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )
        from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
        from app.domains.cv_screening.services.wsi_feedback_generator import get_feedback_generator

        comm_dispatcher = CommunicationDispatcher()
        response_scores = response_scores or []

        # 1 — Resolve seniority from JobVacancy
        seniority_level = "junior"
        candidate_phone = None
        try:
            job = await find_job_vacancy_for_triagem(
                db, session.job_id, session.company_id
            )
            if job and getattr(job, "seniority_level", None):
                seniority_level = job.seniority_level
        except Exception as _e:
            logger.warning(f"[Triagem] Could not resolve seniority: {_e}")

        # 2 — Resolve candidate phone for WhatsApp
        try:
            cand_repo = CandidateRepository(db)
            cand = (
                await cand_repo.get_by_id_str(session.candidate_id)
                if session.candidate_id
                else None
            )
            if cand:
                candidate_phone = getattr(cand, "mobile_phone", None) or getattr(cand, "phone", None)
        except Exception as _e:
            logger.warning(f"[Triagem] Could not resolve candidate phone: {_e}")

        # 3 — Generate structured feedback
        feedback_gen = get_feedback_generator()
        feedback_report = feedback_gen.generate(
            response_scores=response_scores,
            job_title=session.job_title or "a vaga",
            seniority_level=seniority_level,
            candidate_name=session.candidate_name or "Candidato(a)",
        )

        # 4 — Persist feedback_draft
        session.feedback_draft = _json.dumps(feedback_report, ensure_ascii=False)

        # 5 — Chat web: inject as final LIA message in the session
        try:
            feedback_chat_msg = TriagemMessage(
                session_id=session.id,
                sender="lia",
                content=feedback_report["chat_text"],
                message_type="feedback",
                wsi_block=session.current_block,
            )
            db.add(feedback_chat_msg)
            await db.flush()
            actions["chat_feedback"] = "sent"
            logger.info(f"[Triagem] Chat feedback message added for session {session.token}")
        except Exception as _e:
            logger.warning(f"[Triagem] Could not add chat feedback message: {_e}")
            actions["chat_feedback"] = "failed"

        # 6 — Email: rich HTML feedback
        email_result = {"success": False}
        if session.candidate_email:
            try:
                template_path = _os.path.join(
                    _os.path.dirname(__file__),
                    "..", "templates", "triagem_feedback_email.html"
                )
                with open(template_path) as _f:
                    html_template = _f.read()

                # Simple template rendering (no Jinja2 dependency)
                dim_html = ""
                for d in feedback_report["dimensions"]:
                    dim_html += f"""
                    <div class="dimension-card">
                      <div class="dimension-header">
                        <span class="dim-icon">{d['icon']}</span>
                        <span class="dim-title">{d['title']}</span>
                      </div>
                      <div class="dimension-body">
                        <div class="feedback-row">
                          <span class="feedback-label label-strength">✅</span>
                          <div class="feedback-text">
                            <strong>Ponto Forte</strong>{d['strength']}
                          </div>
                        </div>
                        <div class="feedback-row">
                          <span class="feedback-label label-development">🌱</span>
                          <div class="feedback-text">
                            <strong>Área de Desenvolvimento</strong>{d['development']}
                          </div>
                        </div>
                        <div class="feedback-row">
                          <span class="feedback-label label-suggestion">💡</span>
                          <div class="feedback-text">
                            <strong>Sugestão Prática</strong>{d['suggestion']}
                          </div>
                        </div>
                      </div>
                    </div>"""

                platform_email = _os.getenv("MAILGUN_FROM_EMAIL", "noreply@wedotalent.com")
                html_body = (html_template
                    .replace("{{ candidate_name }}", feedback_report["first_name"])
                    .replace("{{ job_title }}", feedback_report["job_title"])
                    .replace("{{ intro_body }}", feedback_report["intro"].replace("\n", "<br>"))
                    .replace("{{ closing }}", feedback_report["closing"].replace("\n", "<br>"))
                    .replace("{{ company_name }}", session.company_name or "WeDOTalent")
                    .replace("{{ reply_email }}", platform_email)
                    .replace("{{ privacy_url }}", "https://wedotalent.com/privacidade")
                    .replace("{{ lgpd_url }}", "https://wedotalent.com/lgpd")
                    .replace("{% for dim in dimensions %}", "")
                    .replace("{% endfor %}", "")
                    .replace("""        <div class="dimension-card">
                      <div class="dimension-header">
                        <span class="dim-icon">{{ dim.icon }}</span>
                        <span class="dim-title">{{ dim.title }}</span>
                      </div>
                      <div class="dimension-body">
                        <div class="feedback-row">
                          <span class="feedback-label label-strength">✅</span>
                          <div class="feedback-text">
                            <strong>Ponto Forte</strong>
                            {{ dim.strength }}
                          </div>
                        </div>
                        <div class="feedback-row">
                          <span class="feedback-label label-development">🌱</span>
                          <div class="feedback-text">
                            <strong>Área de Desenvolvimento</strong>
                            {{ dim.development }}
                          </div>
                        </div>
                        <div class="feedback-row">
                          <span class="feedback-label label-suggestion">💡</span>
                          <div class="feedback-text">
                            <strong>Sugestão Prática</strong>
                            {{ dim.suggestion }}
                          </div>
                        </div>
                      </div>
                    </div>""", dim_html)
                )

                email_result = comm_dispatcher.send_email(
                    to_email=session.candidate_email,
                    subject=f"Feedback da sua triagem — {session.job_title or 'Processo Seletivo'}",
                    body_html=html_body,
                    body_text=feedback_report["plain_text"],
                )
                actions["email_confirmation"] = "sent" if email_result.get("success") else "failed"
                logger.info(
                    f"[Triagem] Feedback email sent to {session.candidate_email} "
                    f"(mock={email_result.get('mock', False)})"
                )
            except Exception as _e:
                logger.warning(f"[Triagem] Could not send HTML feedback email: {_e}")
                # Fallback: plain text email
                email_result = comm_dispatcher.send_email(
                    to_email=session.candidate_email,
                    subject=f"Feedback da sua triagem — {session.job_title or 'Processo Seletivo'}",
                    body_html=f"<pre>{feedback_report['plain_text']}</pre>",
                    body_text=feedback_report["plain_text"],
                )
                actions["email_confirmation"] = "sent" if email_result.get("success") else "failed"

        # 7 — WhatsApp: condensed feedback
        whatsapp_result = {"success": False}
        should_send_whatsapp = (
            candidate_phone and (
                session.invite_channel == "whatsapp"
                or session.invite_channel is None  # default: try
            )
        )
        if should_send_whatsapp:
            try:
                whatsapp_result = comm_dispatcher.send_whatsapp(
                    to_phone=candidate_phone,
                    message=feedback_report["whatsapp_text"],
                )
                logger.info(
                    f"[Triagem] WhatsApp feedback sent to {candidate_phone} "
                    f"(success={whatsapp_result.get('success')})"
                )
            except Exception as _e:
                logger.warning(f"[Triagem] Could not send WhatsApp feedback: {_e}")

        # 8 — Compile channel results
        channels_sent = []
        if actions.get("chat_feedback") == "sent":
            channels_sent.append("chat_web")
        if email_result.get("success"):
            channels_sent.append("email")
        if whatsapp_result.get("success"):
            channels_sent.append("whatsapp")

        actions["confirmation_channels"] = channels_sent
        logger.info(
            f"[Triagem] Feedback delivered via channels: {channels_sent} "
            f"for session {session.token}"
        )

    except Exception as e:
        logger.warning(f"[Triagem] Failed to generate/send feedback: {e}")
        actions["email_confirmation"] = "failed"

    try:
        from app.domains.communication.services.teams_bot import teams_bot
        await teams_bot.notify_triagem_completed(
            candidate_name=session.candidate_name or "Candidato",
            job_title=session.job_title or "Vaga",
            score=session.wsi_final_score,
            classification=session.recommendation or "pendente",
        )
        logger.info(
            f"[Triagem] Recruiter Teams notification sent: "
            f"'Candidato {session.candidate_name} concluiu triagem (score: {session.wsi_final_score})'"
        )
    except Exception as e:
        logger.warning(f"[Triagem] Failed to send Teams recruiter notification: {e}")

    # TeamsProactivityEngine fire-and-forget hook (triagem concluida via DM)
    try:
        import asyncio as _at
        from app.domains.communication.services.teams_proactivity_engine import _safe_teams_hook as _sth, teams_proactivity_engine as _te
        _lp = _at.get_event_loop()
        if _lp.is_running():
            _lp.create_task(_sth(
                _te.on_screening_complete,
                candidate_id=session.candidate_id or "",
                candidate_name=session.candidate_name or "Candidato",
                vacancy_id=session.job_id or "",
                job_title=session.job_title or "Vaga",
                match_score=float(session.wsi_final_score or 0.0),
                recommendation=session.recommendation or "pendente",
                company_id=str(session.company_id or ""),
            ))
    except Exception:
        pass  # Teams hook nao e obrigatorio, nunca bloqueia fluxo principal


    try:
        from app.services.notification_service import (
            NotificationType,
            notification_service,
        )
        score_val = session.wsi_final_score or 0.0
        recommendation = session.recommendation or "pendente"
        notif_type = NotificationType.SUCCESS if score_val >= 7.5 else (
            NotificationType.WARNING if score_val < 5.5 else NotificationType.INFO
        )
        await notification_service.create_notification(
            user_id=session.created_by or "default_user",
            title=f"Triagem concluída: {session.candidate_name or 'Candidato'}",
            message=(
                f"{session.candidate_name or 'Candidato'} concluiu a triagem para "
                f"'{session.job_title or 'Vaga'}'. "
                f"Score WSI: {score_val:.1f} — {recommendation.upper()}."
            ),
            notification_type=notif_type,
            category="screening_completed",
            source_agent="triagem_session_service",
            source_trigger="screening_completed",
            related_job_id=session.job_id,
            related_candidate_id=session.candidate_id,
            action_url=f"/candidates/{session.candidate_id}",
            action_label="Ver Candidato",
            metadata={
                "wsi_score": score_val,
                "recommendation": recommendation,
                "screening_type": "web_chat",
                "session_token": session.token,
            },
            db=db,
        )
        actions["recruiter_notification"] = "sent"
        logger.info(f"[Triagem] Recruiter notification sent via notification_service for session {session.token}")
    except Exception as e:
        logger.warning(f"[Triagem] Failed to send recruiter notification via notification_service: {e}")
        actions["recruiter_notification"] = "failed"

    wsi_session_id: str | None = None
    try:
        wsi_session_id = await _persist_wsi_results(db, session, response_scores)
        if wsi_session_id:
            actions["wsi_persistence"] = "done"
            meta = session.metadata_json or {}
            meta["wsi_session_id"] = wsi_session_id
            meta["wsi_channel"] = "web_chat"
            session.metadata_json = meta
            await db.flush()
            # P0-1: retroalimentar vacancy_candidates.lia_score com score WSI.
            # Conversão de escala: wsi_final_score (0-10) × 10 = lia_score (0-100).
            # Fail-soft: erro de DB não aborta o fluxo principal de triagem.
            if session.candidate_id and session.job_id and session.company_id:
                try:
                    from app.domains.candidates.repositories.vacancy_candidate_repository import (
                        VacancyCandidateRepository,
                    )
                    from app.domains.cv_screening.constants.wsi_scale import (
                        wsi_score_to_lia_scale,
                    )
                    _vc_repo = VacancyCandidateRepository(db)
                    _wsi_lia_score = wsi_score_to_lia_scale(session.wsi_final_score or 0.0)
                    _rowcount = await _vc_repo.update_wsi_lia_score(
                        candidate_id=session.candidate_id,
                        vacancy_id=session.job_id,
                        company_id=session.company_id,
                        lia_score=_wsi_lia_score,
                    )
                    if _rowcount:
                        actions["lia_score_update"] = f"ok:{_wsi_lia_score}"
                        logger.info(
                            "[P0-1] lia_score atualizado: candidate=%s vacancy=%s score=%.1f",
                            session.candidate_id, session.job_id, _wsi_lia_score,
                        )
                    else:
                        actions["lia_score_update"] = "skipped_no_vc_row"
                        logger.warning(
                            "[P0-1] VacancyCandidate nao encontrado: candidate=%s vacancy=%s — lia_score nao atualizado",
                            session.candidate_id, session.job_id,
                        )
                except Exception as _p01_exc:
                    logger.error("[P0-1] lia_score update falhou (fail-soft): %s", _p01_exc)
                    actions["lia_score_update"] = "failed"
            # 2.2: criar LiaOpinion tipo "wsi" — parecer estruturado no parecer de candidato.
            # Fail-soft: falha no insert nao aborta o fluxo de triagem.
            try:
                from app.domains.pipeline.repositories.lia_opinion_repository import (
                    LiaOpinionRepository,
                )
                from app.domains.cv_screening.constants.wsi_scale import (
                    wsi_score_to_lia_scale as _wsi_scale_fn,
                )
                _lio_repo = LiaOpinionRepository(db)
                _wsi_lia_score_22 = _wsi_scale_fn(session.wsi_final_score or 0.0)
                await _lio_repo.create_wsi_opinion(
                    candidate_id=session.candidate_id,
                    company_id=session.company_id,
                    wsi_score=_wsi_lia_score_22,
                    job_vacancy_id=session.job_id,
                    wsi_screening_id=wsi_session_id,
                    recommendation=getattr(session, "recommendation", None),
                )
                actions["lia_opinion_created"] = f"ok:{_wsi_lia_score_22}"
                logger.info(
                    "[2.2] LiaOpinion WSI criado: candidate=%s score=%.1f",
                    session.candidate_id, _wsi_lia_score_22,
                )
            except Exception as _22_exc:
                logger.error("[2.2] LiaOpinion criação falhou (fail-soft): %s", _22_exc)
                actions["lia_opinion_created"] = "failed"
        else:
            actions["wsi_persistence"] = "skipped"
    except Exception as e:
        logger.warning(f"[Triagem] Failed to persist WSI results: {e}")
        actions["wsi_persistence"] = "failed"

    if not wsi_session_id:
        logger.warning(
            "[Triagem] Skipping screening-completed event dispatch — "
            "wsi_session_id not available (persistence failed or was skipped)"
        )
        actions["pipeline_update"] = "skipped_no_wsi_session"
    else:
        try:
            score_val = session.wsi_final_score or 0.0
            recommendation = session.recommendation or "aguardando"
            passed = score_val >= 7.5
            classification_map = {
                "aprovado": "recommended",
                "reprovado": "not_recommended",
                "aguardando": "pending_review",
                "pendente": "pending_review",
            }
            classification = classification_map.get(recommendation, "pending_review")

            wsi_scores: dict[str, Any] = {
                "overall_wsi": score_val,
            }
            for rs in (response_scores or []):
                bt = rs.get("block_type", "behavioral")
                if bt == "technical":
                    wsi_scores.setdefault("technical_wsi", []).append(rs.get("score", 0.0))
                else:
                    wsi_scores.setdefault("behavioral_wsi", []).append(rs.get("score", 0.0))
            if "technical_wsi" in wsi_scores and isinstance(wsi_scores["technical_wsi"], list):
                lst = wsi_scores["technical_wsi"]
                wsi_scores["technical_wsi"] = round(sum(lst) / len(lst) / 2.0, 2) if lst else 0.0
            if "behavioral_wsi" in wsi_scores and isinstance(wsi_scores["behavioral_wsi"], list):
                lst = wsi_scores["behavioral_wsi"]
                wsi_scores["behavioral_wsi"] = round(sum(lst) / len(lst) / 2.0, 2) if lst else 0.0

            dispatcher = _get_event_dispatcher()
            await dispatcher.on_screening_completed(
                candidate_id=session.candidate_id,
                vacancy_id=session.job_id,
                company_id=session.company_id,
                wsi_scores=wsi_scores,
                screening_type="web_chat",
                passed=passed,
                classification=classification,
                session_id=session.token,
                wsi_session_id=wsi_session_id,
            )
            actions["pipeline_update"] = "dispatched_via_event_dispatcher"
            logger.info(
                f"[Triagem] screening-completed event dispatched for "
                f"candidate={session.candidate_id}, score={score_val}, passed={passed}"
            )
            # A2b: publica no barramento Redis para Teams DM + bell notification.
            # Fail-soft: erro de Redis nao aborta o fluxo principal de triagem.
            try:
                from app.shared.messaging.platform_events import (
                    ScreeningCompletedEvent,
                    publish_platform_event,
                )
                await publish_platform_event(ScreeningCompletedEvent(
                    company_id=session.company_id,
                    payload={
                        "candidate_id": session.candidate_id,
                        "vacancy_id": session.job_id,
                        "candidate_name": session.candidate_name or "",
                        "wsi_final_score": score_val,
                        "wsi_scores": wsi_scores,
                    },
                ))
                actions["redis_event"] = "screening.wsi.completed_published"
                logger.info(
                    "[Triagem] A2b: screening.wsi.completed published to Redis"
                    " for candidate=%s", session.candidate_id,
                )
            except Exception as _a2b_exc:
                logger.warning(
                    "[Triagem] A2b: screening event Redis publish failed (fail-soft): %s",
                    _a2b_exc,
                )
                actions["redis_event"] = "publish_failed"
        except Exception as e:
            logger.warning(f"[Triagem] Failed to dispatch screening-completed event: {e}")
            actions["pipeline_update"] = "event_dispatch_failed"

    return actions


async def _persist_wsi_results(
    db: AsyncSession,
    session: TriagemSession,
    response_scores: list[dict[str, Any]],
) -> str | None:
    """
    Persist screening results to WSI tables (wsi_sessions, wsi_questions,
    wsi_response_analyses, wsi_results) following the canonical WSI schema.

    Schema constraints respected:
    - wsi_sessions.screening_type IN ('voice', 'chat', 'hybrid')
    - wsi_sessions.mode IN ('compact', 'compact_plus')
    - wsi_response_analyses.question_id FK → wsi_questions(id)
    - scores in [1..5] range
    - wsi_results.classification IN ('excelente', 'alto', 'medio', 'regular', 'baixo')

    Returns the wsi_session_id string if the wsi_sessions row was successfully
    created; returns None on any critical failure so callers can skip the
    event-dispatcher dispatch.
    """
    if not session.candidate_id or not session.job_id:
        logger.warning("[Triagem] Cannot persist WSI results: missing candidate_id or job_id")
        return None

    wsi_session_id = f"system:{uuid.uuid4()}"
    meta = session.metadata_json or {}
    qs_version = meta.get("wsi_question_set_version")
    qs_id = meta.get("wsi_question_set_id")
    score_val = session.wsi_final_score or 0.0

    screening_config = _get_screening_config(session)
    raw_mode = _resolve_screening_mode(screening_config)
    _mode_map = {"compact": "compact", "compact_plus": "compact_plus", "full": "compact_plus"}
    mode = _mode_map.get(raw_mode, "compact")

    from app.domains.voice.repositories.wsi_repository import WsiRepository
    wsi_repo = WsiRepository(db)
    try:
        await wsi_repo.insert_session_with_completed_at(
            session_id=wsi_session_id,
            candidate_id=session.candidate_id,
            job_vacancy_id=session.job_id,
            screening_type="chat",
            mode=mode,
            status="completed",
            question_set_version=int(qs_version) if qs_version else None,
            question_set_id=qs_id,
            completed_at=session.completed_at or datetime.utcnow(),
        )
    except Exception as exc:
        logger.error(f"[Triagem] wsi_sessions insert failed — aborting WSI persistence: {exc}")
        return None

    technical_scores: list[float] = []
    behavioral_scores: list[float] = []

    for seq, rs in enumerate(response_scores or [], start=1):
        block_type = rs.get("block_type", "behavioral")
        competency = rs.get("competency", "general")
        raw_score = float(rs.get("score", 6.0))
        score_0_10 = max(0.0, min(10.0, round(raw_score, 2)))
        question_text = rs.get("question_text") or f"Questão {seq} — {competency}"
        response_text = rs.get("response_text") or ""

        question_id = str(uuid.uuid4())
        if block_type == "technical":
            framework = "CBI"
            q_type = "autodeclaration"
        else:
            framework = "CBI"
            q_type = "contextual"

        try:
            await wsi_repo.insert_question_full(
                question_id=question_id,
                session_id=wsi_session_id,
                competency=competency,
                framework=framework,
                question_type=q_type,
                question_text=question_text[:2000],
                weight=1.0,
                sequence_order=seq,
            )
        except Exception as exc:
            logger.warning(f"[Triagem] wsi_questions insert failed (seq={seq}): {exc}")
            if block_type == "technical":
                technical_scores.append(score_0_10)
            else:
                behavioral_scores.append(score_0_10)
            continue

        analysis_id = str(uuid.uuid4())
        try:
            await wsi_repo.insert_response_analysis_full(
                analysis_id=analysis_id,
                session_id=wsi_session_id,
                question_id=question_id,
                candidate_id=session.candidate_id,
                job_vacancy_id=session.job_id,
                competency=competency,
                response_text=response_text,
                autodeclaration_score=score_0_10,
                context_score=score_0_10,
                bloom_level=max(1, min(5, rs.get("bloom_level", 2))),
                dreyfus_level=max(1, min(5, rs.get("dreyfus_level", 2))),
                evidences_json=json.dumps(rs.get("evidences", [])),
                red_flags_json=json.dumps(rs.get("red_flags", [])),
                consistency_penalty=0.0,
                final_score=score_0_10,
                justification=rs.get("justification", "Score calculado a partir da resposta no chat web"),
            )
        except Exception as exc:
            logger.warning(f"[Triagem] wsi_response_analyses insert failed (seq={seq}): {exc}")

        if block_type == "technical":
            technical_scores.append(score_0_10)
        else:
            behavioral_scores.append(score_0_10)

    tech_wsi = max(0.0, min(10.0, round(sum(technical_scores) / len(technical_scores), 2))) if technical_scores else max(0.0, min(10.0, round(score_val, 2)))
    beh_wsi = max(0.0, min(10.0, round(sum(behavioral_scores) / len(behavioral_scores), 2))) if behavioral_scores else max(0.0, min(10.0, round(score_val, 2)))
    overall_wsi = max(0.0, min(10.0, round(score_val, 2)))

    # P1-1 (audit 2026-06-05): bandas em escala 0-10 (CHECK aceita
    # excepcional/excelente/alto/medio/abaixo_da_media/regular/baixo; FE colore
    # excepcional..abaixo_da_media). 3-tier visual do FE: verde>=7.5, amarelo>=6.
    if overall_wsi >= 9.0:
        wsi_classification = "excepcional"
    elif overall_wsi >= 7.5:
        wsi_classification = "excelente"
    elif overall_wsi >= 6.0:
        wsi_classification = "alto"
    elif overall_wsi >= 4.5:
        wsi_classification = "medio"
    elif overall_wsi >= 3.0:
        wsi_classification = "abaixo_da_media"
    else:
        wsi_classification = "baixo"

    try:
        result_id = str(uuid.uuid4())
        await wsi_repo.insert_result_full(
            result_id=result_id,
            session_id=wsi_session_id,
            candidate_id=session.candidate_id,
            job_vacancy_id=session.job_id,
            technical_wsi=tech_wsi,
            behavioral_wsi=beh_wsi,
            overall_wsi=overall_wsi,
            classification=wsi_classification,
            percentile=None,
        )
    except Exception as exc:
        logger.error(f"[Triagem] wsi_results insert failed: {exc}")
        return None

    await db.flush()
    logger.info(
        f"[Triagem] WSI results persisted: wsi_session={wsi_session_id}, "
        f"tech={tech_wsi}, beh={beh_wsi}, overall={overall_wsi}, class={wsi_classification}"
    )
    return wsi_session_id


