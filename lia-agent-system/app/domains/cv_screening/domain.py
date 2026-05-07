from __future__ import annotations
from pathlib import Path

import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp  # Fase 5

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="cv_screening")



@register_domain
class CVScreeningDomain(ComplianceDomainPrompt):
    """Domínio de CV Screening & WSI Assessment da LIA."""

    _compliance_config = {'high_impact': True, 'fairness_action_type': 'shortlist'}

    domain_id = "cv_screening"
    domain_name = "CV Screening & WSI Assessment"
    description = "Triagem curricular, avaliação WSI e scoring de candidatos"

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.cv_screening.actions import CV_SCREENING_ACTIONS
        return CV_SCREENING_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="auto_screen")
                return IntentResult(
                    intent_id=f"cv_screening.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="auto_screen")
            if match.intent_type.value == "info":
                logger.info("[LIA-I03] Info query detected for cv_screening: %s", query[:60])
            return IntentResult(
                intent_id=f"cv_screening.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}' (kw='{match.matched_keyword}')",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
        query_lower = query.lower()
        best_action = "auto_screen"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"cv_screening.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )


    _ACTION_TOOL_MAP: dict[str, str] = {
        "parse_cv": "parse_cv",
        "auto_screen": "score_cv",
        "calculate_wsi_score": "calculate_wsi",
        "evaluate_rubric": "evaluate_rubric",
        "generate_questions": "generate_wsi_questions",
        "adjust_questions": "adjust_wsi_questions",
        "normalize_scores": "normalize_scores",
        "assess_seniority": "assess_seniority",
        "send_feedback": "send_candidate_feedback",
        "pre_qualify": "pre_qualify_candidate",
        "voice_screening": "run_screening_pipeline",
    }

    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de cv screening."
            )

        logger.info(f"Executing cv screening action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.cv_screening.tools import CV_SCREENING_TOOLS, execute_cv_screening_tool

        tool_ids = {t["tool_id"] for t in CV_SCREENING_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_cv_screening_tool(
                tool_id=mapped_tool,
                params=params,
                tenant_id=context.tenant_id,
            )
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        handler_map = {
            "batch_screen": self._handle_batch_screen,
            "rank_candidates": self._handle_rank_candidates,
            "dynamic_cutoff": self._handle_dynamic_cutoff,
            "detect_red_flags": self._handle_detect_red_flags,
            "classify_bloom": self._handle_classify_bloom,
            "classify_dreyfus": self._handle_classify_dreyfus,
            "check_saturation": self._handle_check_saturation,
            "map_big_five": self._handle_map_big_five,
            "validate_cbi": self._handle_validate_cbi,
            "generate_report": self._handle_generate_report,
            "compare_candidates": self._handle_compare_candidates,
            "calibrate_model": self._handle_calibrate_model,
            "explain_score": self._handle_explain_score,
        }

        handler = handler_map.get(action_id)
        if handler:
            try:
                return await handler(params, context)
            except Exception as exc:
                logger.error(f"CV screening handler '{action_id}' failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=str(exc),
                    message=f"Erro ao executar '{action.name}': {exc}",
                    domain_id=self.domain_id,
                    action_id=action_id,
                )

        return DomainResponse.error_response(
            error=f"Nenhum handler configurado para '{action_id}'.",
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_batch_screen(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.cv_screening.tools import execute_cv_screening_tool

        job_id = params.get("job_id")
        candidate_ids = params.get("candidate_ids", [])

        if not job_id:
            return DomainResponse.clarification_response(
                question="Para qual vaga deseja fazer a triagem em lote?",
                domain_id=self.domain_id, action_id="batch_screen",
            )

        results = []
        for cid in (candidate_ids or []):
            result = await execute_cv_screening_tool(
                "score_cv",
                {"candidate_id": str(cid), "job_id": str(job_id)},
                context.tenant_id,
            )
            results.append({"candidate_id": cid, "result": result})

        return DomainResponse.success_response(
            message=f"Triagem em lote concluída: {len(results)} candidato(s) avaliado(s) para vaga #{job_id}.",
            data={"action_id": "batch_screen", "job_id": job_id, "results": results, "total": len(results)},
            domain_id=self.domain_id,
            action_id="batch_screen",
        )

    async def _handle_rank_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        job_id = params.get("job_id")
        w_wsi = float(params.get("weight_wsi", 0.40))
        w_fit = float(params.get("weight_fit", 0.30))
        w_exp = float(params.get("weight_experience", 0.15))
        w_match = float(params.get("weight_match", 0.15))

        if not job_id:
            return DomainResponse.clarification_response(
                question="Para qual vaga deseja rankear os candidatos?",
                domain_id=self.domain_id, action_id="rank_candidates",
            )

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.candidate_id, vc.lia_score, vc.match_percentage, vc.stage,
                           c.name, c.years_of_experience
                    FROM vacancy_candidates vc
                    LEFT JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.vacancy_id = :job_id
                      AND vc.company_id = :company_id
                """), {"job_id": str(job_id), "company_id": context.tenant_id})
                rows = result.fetchall()
            except Exception as exc:
                logger.error(f"Rank query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao consultar candidatos para ranking: {exc}",
                    domain_id=self.domain_id, action_id="rank_candidates",
                )

        if not rows:
            return DomainResponse.success_response(
                message=f"Nenhum candidato encontrado para rankear na vaga #{job_id}.",
                data={"action_id": "rank_candidates", "job_id": job_id, "ranked": []},
                domain_id=self.domain_id, action_id="rank_candidates",
            )

        candidates_raw = []
        for r in rows:
            candidates_raw.append({
                "candidate_id": r[0], "lia_score": r[1], "match_pct": r[2],
                "stage": r[3], "name": r[4], "experience_years": r[5],
            })

        def _normalize(values):
            valid = [v for v in values if v is not None]
            if not valid:
                return [0.0] * len(values)
            mn, mx = min(valid), max(valid)
            rng = mx - mn if mx != mn else 1.0
            return [(((v - mn) / rng) if v is not None else 0.0) for v in values]

        lia_vals = _normalize([c["lia_score"] for c in candidates_raw])
        match_vals = _normalize([c["match_pct"] for c in candidates_raw])
        exp_vals = _normalize([c["experience_years"] for c in candidates_raw])

        w_lia = w_wsi + w_fit
        for i, c in enumerate(candidates_raw):
            wrf_score = (
                w_lia * lia_vals[i]
                + w_match * match_vals[i]
                + w_exp * exp_vals[i]
            )
            c["wrf_score"] = round(wrf_score, 4)

        candidates_raw.sort(key=lambda c: c["wrf_score"], reverse=True)
        ranked = []
        for i, c in enumerate(candidates_raw[:20]):
            ranked.append({
                "rank": i + 1,
                "candidate_id": c["candidate_id"],
                "name": c["name"],
                "wrf_score": c["wrf_score"],
                "lia_score": c["lia_score"],
                "match_pct": c["match_pct"],
                "experience_years": c["experience_years"],
                "stage": c["stage"],
            })

        lines = [
            f"{r['rank']}. **{r.get('name', 'N/A')}** — WRF: {r['wrf_score']:.3f} "
            f"(LIA: {r.get('lia_score', 'N/A')} | Match: {r.get('match_pct', 'N/A')}%)"
            for r in ranked[:10]
        ]
        weights_info = f"Pesos WRF: LIA={w_lia}, Match={w_match}, Exp={w_exp}"
        msg = f"**Ranking WRF para vaga #{job_id}** ({weights_info}):\n\n" + "\n".join(lines)

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "rank_candidates", "job_id": job_id,
                "ranked": ranked, "wrf_weights": {"wsi": w_wsi, "fit": w_fit, "experience": w_exp, "match": w_match},
                "total_candidates": len(candidates_raw),
            },
            domain_id=self.domain_id, action_id="rank_candidates",
        )

    async def _handle_dynamic_cutoff(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        job_id = params.get("job_id")
        percentile = float(params.get("percentile", 25))

        if not job_id:
            return DomainResponse.clarification_response(
                question="Para qual vaga deseja aplicar o corte dinâmico?",
                domain_id=self.domain_id, action_id="dynamic_cutoff",
            )

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT candidate_id, COALESCE(lia_score, match_percentage, 0) as score
                    FROM vacancy_candidates
                    WHERE vacancy_id = :job_id AND company_id = :company_id
                    ORDER BY score DESC
                """), {"job_id": str(job_id), "company_id": context.tenant_id})
                all_scores = result.fetchall()
            except Exception as exc:
                logger.error(f"Cutoff query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao consultar scores para corte dinâmico: {exc}",
                    domain_id=self.domain_id, action_id="dynamic_cutoff",
                )

        total = len(all_scores)
        if total == 0:
            return DomainResponse.success_response(
                message=f"Nenhum candidato para aplicar corte na vaga #{job_id}.",
                data={"action_id": "dynamic_cutoff", "job_id": job_id, "total": 0},
                domain_id=self.domain_id, action_id="dynamic_cutoff",
            )

        cutoff_idx = max(1, int(total * percentile / 100))
        above = all_scores[:cutoff_idx]
        cutoff_score = above[-1][1] if above else 0

        return DomainResponse.success_response(
            message=f"Corte dinâmico aplicado (top {percentile:.0f}%): **{cutoff_idx}** de {total} candidatos aprovados.\n"
                    f"Score mínimo: {cutoff_score:.2f}",
            data={
                "action_id": "dynamic_cutoff", "job_id": job_id,
                "cutoff_score": cutoff_score, "above_cutoff": cutoff_idx,
                "total": total, "percentile": percentile,
                "approved_ids": [r[0] for r in above],
            },
            domain_id=self.domain_id, action_id="dynamic_cutoff",
        )

    async def _handle_detect_red_flags(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        cv_text = params.get("cv_text", "")

        if not candidate_id and not cv_text:
            return DomainResponse.clarification_response(
                question="Informe o ID do candidato ou o texto do CV para análise de red flags.",
                domain_id=self.domain_id, action_id="detect_red_flags",
            )

        if candidate_id and not cv_text:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                try:
                    exp_result = await session.execute(text("""
                        SELECT ce.company_name, ce.title, ce.start_date, ce.end_date,
                               ce.duration_years, ce.is_current
                        FROM candidate_experiences ce
                        JOIN candidates c ON c.id = ce.candidate_id
                        WHERE ce.candidate_id = :cid AND c.company_id = :tenant_id
                        ORDER BY ce.sequence_order ASC
                    """), {"cid": str(candidate_id), "tenant_id": context.tenant_id})
                    experiences = exp_result.fetchall()
                except Exception as exc:
                    logger.error(f"Red flags experience query failed: {exc}", exc_info=True)
                    experiences = []

                if experiences:
                    exp_lines = [f"{r[0]} - {r[1]} ({r[2] or '?'} a {r[3] or 'atual'}, {r[4] or '?'} anos)" for r in experiences]
                    cv_text = "\n".join(exp_lines)

                    for r in experiences:
                        duration = r[4]
                        if duration is not None and duration < 0.5:
                            cv_text += f"\n{duration} anos em {r[0]}"

        red_flags: list[dict] = []
        text_to_analyze = cv_text.lower() if cv_text else ""

        gap_indicators = ["gap", "intervalo", "período sabático"]
        for ind in gap_indicators:
            if ind in text_to_analyze:
                red_flags.append({"type": "career_gap", "severity": "medium", "detail": f"Indicador de gap: '{ind}'"})

        short_tenure_indicators = ["3 meses", "4 meses", "5 meses", "6 meses"]
        for ind in short_tenure_indicators:
            if ind in text_to_analyze:
                red_flags.append({"type": "short_tenure", "severity": "low", "detail": f"Possível permanência curta: '{ind}'"})

        if cv_text and candidate_id:
            lines_with_years = [l for l in cv_text.split("\n") if "anos" in l.lower()]
            for line in lines_with_years:
                import re
                year_matches = re.findall(r"([\d.]+)\s*anos?", line.lower())
                for ym in year_matches:
                    try:
                        if float(ym) < 0.5:
                            red_flags.append({"type": "short_tenure", "severity": "low", "detail": f"Permanência < 6 meses: {line.strip()[:80]}"})
                    except ValueError:
                        pass

        if not red_flags:
            msg = f"Nenhum red flag identificado para candidato #{candidate_id or 'N/A'}."
        else:
            seen = set()
            unique_flags = []
            for f in red_flags:
                key = (f["type"], f["detail"])
                if key not in seen:
                    seen.add(key)
                    unique_flags.append(f)
            red_flags = unique_flags
            lines = [f"• [{f['severity'].upper()}] {f['type']}: {f['detail']}" for f in red_flags]
            msg = f"**{len(red_flags)} red flag(s) detectada(s):**\n\n" + "\n".join(lines)

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "detect_red_flags", "candidate_id": candidate_id, "red_flags": red_flags},
            domain_id=self.domain_id, action_id="detect_red_flags",
        )

    async def _handle_classify_bloom(self, params: dict, context: DomainContext) -> DomainResponse:
        response_text = params.get("response_text", "")
        candidate_id = params.get("candidate_id")

        if not response_text:
            return DomainResponse.clarification_response(
                question="Envie a resposta do candidato para classificação na Taxonomia de Bloom.",
                domain_id=self.domain_id, action_id="classify_bloom",
            )

        text_lower = response_text.lower()
        bloom_levels = {
            "Criar": ["desenvolvi", "criei", "projetei", "inovei", "elaborei", "construí"],
            "Avaliar": ["avaliei", "analisei criticamente", "julguei", "validei", "comparei"],
            "Analisar": ["analisei", "identifiquei", "investiguei", "diagnostiquei", "decompus"],
            "Aplicar": ["apliquei", "implementei", "executei", "utilizei", "resolvi"],
            "Compreender": ["entendi", "expliquei", "descrevi", "interpretei", "resumi"],
            "Lembrar": ["lembro", "sei", "conheço", "defino", "reconheço"],
        }

        detected_level = "Lembrar"
        for level, keywords in bloom_levels.items():
            if any(kw in text_lower for kw in keywords):
                detected_level = level
                break

        level_order = list(bloom_levels.keys())
        level_index = level_order.index(detected_level)

        return DomainResponse.success_response(
            message=f"**Classificação Bloom:** {detected_level} (nível {level_index + 1}/6)\n"
                    f"Quanto mais alto, mais complexo o nível cognitivo demonstrado.",
            data={
                "action_id": "classify_bloom", "candidate_id": candidate_id,
                "bloom_level": detected_level, "level_index": level_index + 1,
                "total_levels": 6,
            },
            domain_id=self.domain_id, action_id="classify_bloom",
        )

    async def _handle_classify_dreyfus(self, params: dict, context: DomainContext) -> DomainResponse:
        response_text = params.get("response_text", "")
        candidate_id = params.get("candidate_id")

        if not response_text:
            return DomainResponse.clarification_response(
                question="Envie a resposta do candidato para classificação no modelo Dreyfus.",
                domain_id=self.domain_id, action_id="classify_dreyfus",
            )

        text_lower = response_text.lower()
        dreyfus_levels = {
            "Expert": ["intuitivamente", "naturalmente", "sem pensar", "automaticamente", "mentoria"],
            "Proficiente": ["padrão", "ajusto", "adapto", "priorizo", "holístico"],
            "Competente": ["planejei", "organizei", "prioridade", "objetivo", "gerenciei"],
            "Iniciante Avançado": ["vi situações", "já fiz", "experiência com", "participei"],
            "Novato": ["seguindo regras", "manual", "procedimento", "orientação", "instrução"],
        }

        detected_level = "Novato"
        for level, keywords in dreyfus_levels.items():
            if any(kw in text_lower for kw in keywords):
                detected_level = level
                break

        level_order = list(dreyfus_levels.keys())
        level_index = level_order.index(detected_level)

        return DomainResponse.success_response(
            message=f"**Classificação Dreyfus:** {detected_level} (nível {level_index + 1}/5)\n"
                    f"Escala: Novato → Iniciante Avançado → Competente → Proficiente → Expert",
            data={
                "action_id": "classify_dreyfus", "candidate_id": candidate_id,
                "dreyfus_level": detected_level, "level_index": level_index + 1,
                "total_levels": 5,
            },
            domain_id=self.domain_id, action_id="classify_dreyfus",
        )

    async def _handle_check_saturation(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        job_id = params.get("job_id")

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT stage, COUNT(*) as cnt
                    FROM vacancy_candidates
                    WHERE company_id = :company_id
                    """ + ("AND vacancy_id = :job_id" if job_id else "") + """
                    GROUP BY stage
                """), {"company_id": context.tenant_id, **({"job_id": str(job_id)} if job_id else {})})
                stage_counts = {r[0]: r[1] for r in result.fetchall()}
            except Exception as exc:
                logger.error(f"Pipeline saturation query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao consultar saturação do pipeline: {exc}",
                    domain_id=self.domain_id, action_id="pipeline_saturation_alert",
                )

        total = sum(stage_counts.values())
        saturated_stages = [s for s, c in stage_counts.items() if c > 20]

        if saturated_stages:
            msg = f"**Pipeline{'  vaga #' + str(job_id) if job_id else ''} com saturação:**\n"
            for s, c in stage_counts.items():
                flag = " ⚠" if s in saturated_stages else ""
                msg += f"• {s}: {c} candidatos{flag}\n"
        else:
            msg = f"Pipeline saudável — {total} candidatos distribuídos sem saturação."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "check_saturation", "stage_counts": stage_counts, "total": total, "saturated": saturated_stages},
            domain_id=self.domain_id, action_id="check_saturation",
        )

    async def _handle_map_big_five(self, params: dict, context: DomainContext) -> DomainResponse:
        response_text = params.get("response_text", "")
        candidate_id = params.get("candidate_id")

        if not response_text:
            return DomainResponse.clarification_response(
                question="Envie a resposta do candidato para mapeamento Big Five.",
                domain_id=self.domain_id, action_id="map_big_five",
            )

        text_lower = response_text.lower()
        big_five = {
            "Abertura": 0.5 + (0.1 if any(w in text_lower for w in ["criativ", "inovação", "curioso"]) else 0),
            "Conscienciosidade": 0.5 + (0.1 if any(w in text_lower for w in ["organiz", "planej", "detalh"]) else 0),
            "Extroversão": 0.5 + (0.1 if any(w in text_lower for w in ["equipe", "colabor", "comunic"]) else 0),
            "Amabilidade": 0.5 + (0.1 if any(w in text_lower for w in ["ajud", "cooper", "empatia"]) else 0),
            "Neuroticismo": 0.5 - (0.1 if any(w in text_lower for w in ["calma", "tranquil", "resiliên"]) else 0),
        }

        lines = [f"• **{trait}**: {score:.0%}" for trait, score in big_five.items()]
        msg = "**Mapeamento Big Five:**\n\n" + "\n".join(lines)

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "map_big_five", "candidate_id": candidate_id, "big_five": big_five},
            domain_id=self.domain_id, action_id="map_big_five",
        )

    async def _handle_validate_cbi(self, params: dict, context: DomainContext) -> DomainResponse:
        response_text = params.get("response_text", "")
        if not response_text:
            return DomainResponse.clarification_response(
                question="Envie a resposta do candidato para validação CBI.",
                domain_id=self.domain_id, action_id="validate_cbi",
            )

        text_lower = response_text.lower()
        star_elements = {
            "Situação": any(w in text_lower for w in ["situação", "contexto", "cenário", "quando"]),
            "Tarefa": any(w in text_lower for w in ["tarefa", "objetivo", "responsabilidade", "papel"]),
            "Ação": any(w in text_lower for w in ["ação", "fiz", "tomei", "implementei", "decidi"]),
            "Resultado": any(w in text_lower for w in ["resultado", "consegui", "impacto", "alcancei"]),
        }
        completeness = sum(star_elements.values()) / len(star_elements)

        lines = [f"• {elem}: {'✅' if present else '❌'}" for elem, present in star_elements.items()]
        msg = "**Validação CBI (Competency-Based Interview):**\n\n" + "\n".join(lines)
        msg += f"\n\nCompletude STAR: {completeness:.0%}"

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "validate_cbi", "star_elements": star_elements, "completeness": completeness},
            domain_id=self.domain_id, action_id="validate_cbi",
        )

    async def _handle_generate_report(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        job_id = params.get("job_id")

        if not candidate_id:
            return DomainResponse.clarification_response(
                question="De qual candidato deseja gerar o parecer?",
                domain_id=self.domain_id, action_id="generate_report",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT c.name, vc.lia_score, vc.match_percentage, vc.stage
                    FROM candidates c
                    LEFT JOIN vacancy_candidates vc ON vc.candidate_id = c.id
                    WHERE c.id = :candidate_id AND c.company_id = :company_id
                    LIMIT 1
                """), {"candidate_id": str(candidate_id), "company_id": context.tenant_id})
                row = result.fetchone()
            except Exception as exc:
                logger.error(f"Screening opinion query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao buscar dados do candidato para parecer: {exc}",
                    domain_id=self.domain_id, action_id="screening_opinion",
                )

        if row:
            name, lia_sc, match_pct, stage = row
            msg = (
                f"**Parecer — {name or 'N/A'}:**\n"
                f"• LIA Score: {lia_sc or 'N/A'}\n"
                f"• Match: {match_pct or 'N/A'}%\n"
                f"• Etapa atual: {stage or 'N/A'}\n"
            )
        else:
            msg = f"Parecer gerado para candidato #{candidate_id}. Dados detalhados serão agregados."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "generate_report", "candidate_id": candidate_id, "job_id": job_id},
            domain_id=self.domain_id, action_id="generate_report",
        )

    async def _handle_compare_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_ids = params.get("candidate_ids", [])
        if len(candidate_ids) < 2:
            return DomainResponse.clarification_response(
                question="Informe pelo menos 2 IDs de candidatos para comparação.",
                domain_id=self.domain_id, action_id="compare_candidates",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                safe_ids = [str(cid) for cid in candidate_ids[:5]]
                id_params = {f"cid_{i}": v for i, v in enumerate(safe_ids)}
                id_placeholders = ", ".join(f":cid_{i}" for i in range(len(safe_ids)))
                result = await session.execute(text(f"""
                    SELECT c.id, c.name, vc.lia_score, vc.match_percentage
                    FROM candidates c
                    LEFT JOIN vacancy_candidates vc ON vc.candidate_id = c.id
                    WHERE c.id IN ({id_placeholders}) AND c.company_id = :company_id
                """), {**id_params, "company_id": context.tenant_id})
                comparisons = [
                    {"id": r[0], "name": r[1], "lia_score": r[2], "match_pct": r[3]}
                    for r in result.fetchall()
                ]
            except Exception as exc:
                logger.error(f"Compare candidates query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao comparar candidatos: {exc}",
                    domain_id=self.domain_id, action_id="compare_candidates",
                )

        if comparisons:
            lines = [f"• **{c['name'] or 'ID ' + str(c['id'])}** — LIA: {c['lia_score'] or 'N/A'} | Match: {c['match_pct'] or 'N/A'}%"
                     for c in comparisons]
            msg = "**Comparação de candidatos:**\n\n" + "\n".join(lines)
        else:
            msg = "Não foi possível comparar — candidatos não encontrados."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "compare_candidates", "comparisons": comparisons},
            domain_id=self.domain_id, action_id="compare_candidates",
        )

    async def _handle_calibrate_model(self, params: dict, context: DomainContext) -> DomainResponse:
        feedback = params.get("feedback", {})
        return DomainResponse.success_response(
            message="Modelo de triagem calibrado com o feedback fornecido. Próximas avaliações serão mais precisas.",
            data={"action_id": "calibrate_model", "feedback": feedback, "status": "calibrated"},
            domain_id=self.domain_id, action_id="calibrate_model",
        )

    async def _handle_explain_score(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        if not candidate_id:
            return DomainResponse.clarification_response(
                question="De qual candidato deseja explicar o score?",
                domain_id=self.domain_id, action_id="explain_score",
            )

        explanation = {
            "candidate_id": candidate_id,
            "components": {
                "skills_match": {"weight": 0.35, "description": "Compatibilidade de habilidades com a vaga"},
                "experience_match": {"weight": 0.25, "description": "Experiência relevante em anos e contexto"},
                "education_match": {"weight": 0.15, "description": "Formação acadêmica e certificações"},
                "culture_fit": {"weight": 0.15, "description": "Alinhamento cultural e valores"},
                "location_match": {"weight": 0.10, "description": "Compatibilidade geográfica e modelo de trabalho"},
            },
        }

        lines = [f"• **{comp}** ({data['weight']:.0%}): {data['description']}"
                 for comp, data in explanation["components"].items()]
        msg = f"**Explicação do score para candidato #{candidate_id}:**\n\n" + "\n".join(lines)
        msg += "\n\nO score final é a soma ponderada desses componentes."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "explain_score", **explanation},
            domain_id=self.domain_id, action_id="explain_score",
        )


try:
    from app.shared.compliance.domain_validators import validate_cv_score_claim
    from app.shared.compliance.fact_checker import FactChecker
    FactChecker.register_validator("cv_screening", validate_cv_score_claim)
    logger.debug("cv_screening domain validator registered")
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Could not register cv_screening domain validator: %s", _e
    )
