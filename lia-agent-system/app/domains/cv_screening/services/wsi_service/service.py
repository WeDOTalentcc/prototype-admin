"""
WSI Service - Main orchestrator combining all WSI components.
"""
import json
import logging
from typing import Any, Literal

from .models import (
    safe_json_parse,
    CandidateFeedback,
    Competency,
    CompetencySuggestion,
    ResponseAnalysis,
    StructuredReport,
    WSIQuestion,
    WSIResult,
    normalize_weights,
)
from .question_generator import WSIQuestionGenerator
from .response_analyzer import WSIResponseAnalyzer
from .score_calculator import WSIScoreCalculator
from .report_generator import WSIReportGenerator

from app.domains.ai.services.llm import llm_service

logger = logging.getLogger(__name__)


def _wsi_fairness_check(text: str):
    """FairnessGuard.check lazy + fail-open (Consolidacao WSI Fase 2.3).

    Portado do fork job_creation/nodes/wsi_questions.py para o canonico —
    single source of truth de fairness. Retorna FairnessCheckResult ou None
    (fail-open: nunca bloqueia o fluxo se o guard estiver indisponivel). O
    contador fairness_blocks_total ja e incrementado dentro de .check().
    """
    if not text or not text.strip():
        return None
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        return FairnessGuard().check(text)
    except Exception as exc:  # noqa: BLE001 — fail-open
        logger.warning("[WSIService] FairnessGuard indisponivel (fail-open): %s", exc)
        return None


class WSIService:
    """
    Serviço completo de aplicação da metodologia WSI.
    
    Responsabilidades:
    1. Analisar JD e sugerir competências
    2. Gerar perguntas científicas baseadas em frameworks
    3. Analisar respostas semanticamente (scoring 1-5)
    4. Calcular WSI (média ponderada)
    5. Gerar pareceres estruturados
    6. Gerar feedbacks construtivos para candidatos
    """
    
    def __init__(self):
        self.llm = llm_service
        self.question_generator = WSIQuestionGenerator(self.llm)
        self.response_analyzer = WSIResponseAnalyzer(self.llm)
        self.score_calculator = WSIScoreCalculator()
        self.report_generator = WSIReportGenerator(self.llm)
    
    async def analyze_jd_and_suggest_competencies(
        self,
        job_description: str,
        company_culture: dict | None = None,
        seniority: Literal["junior", "pleno", "senior", "lead", "executive"] = "pleno"
    ) -> CompetencySuggestion:
        """
        ETAPA 1: Analisa JD e sugere competências automaticamente.
        
        Usa NLP para extrair:
        - Hard skills (Python, React, AWS, etc.)
        - Soft skills (liderança, comunicação, etc.)
        - Nível de senioridade
        - Fit cultural esperado
        
        Args:
            job_description: Texto completo do JD
            company_culture: Valores e cultura da empresa
            seniority: Nível da vaga
            
        Returns:
            CompetencySuggestion com 5-7 competências sugeridas
        """
        prompt = f"""Analise este Job Description e sugira as competências mais importantes para avaliação em triagem.

JD:
{job_description}

Cultura da empresa:
{company_culture or "Não fornecida"}

Nível da vaga: {seniority}

Sua tarefa:
1. Extraia as 5 competências TÉCNICAS mais críticas para a vaga (hard skills)
2. Extraia as 5 competências COMPORTAMENTAIS mais relevantes para a vaga
   - Pode classificar cada uma como "behavioral" (soft skill interpessoal) ou "cultural" (fit com valores/cultura)
   - Ordene da mais crítica para a menos crítica conforme o perfil da vaga
3. Sugira pesos (total = 1.0):
   - 60% para técnicas (distribuir entre as 5, ex: 0.18, 0.15, 0.12, 0.10, 0.05)
   - 40% para comportamentais/culturais (distribuir entre as 5, ex: 0.12, 0.10, 0.08, 0.06, 0.04)

As 5 comportamentais garantem que tanto no modo compacto (6 perguntas) quanto no modo completo (10 perguntas)
a metodologia possa selecionar as mais relevantes conforme o perfil específico da vaga.

Responda em JSON:
{{
  "technical_competencies": [
    {{"name": "Python", "weight": 0.20, "is_critical": true}},
    {{"name": "Django/FastAPI", "weight": 0.15, "is_critical": true}},
    {{"name": "PostgreSQL", "weight": 0.10, "is_critical": false}},
    {{"name": "AWS", "weight": 0.10, "is_critical": false}},
    {{"name": "Docker", "weight": 0.05, "is_critical": false}}
  ],
  "behavioral_competencies": [
    {{"name": "Comunicação Assertiva", "weight": 0.10}},
    {{"name": "Colaboração em Equipe", "weight": 0.08}},
    {{"name": "Gestão de Conflito", "weight": 0.08}},
    {{"name": "Adaptabilidade", "weight": 0.07}},
    {{"name": "Orientação a Resultados", "weight": 0.07}}
  ],
  "cultural_competencies": [],
  "confidence_score": 0.95
}}"""

        content_str = await self.llm.safe_invoke(prompt, provider="claude")
        # Robustez canonica (2026-05-31): o LLM pode devolver JSON cercado por
        # markdown; json.loads cru falha com "char 0". Strip defensivo beneficia
        # toda a plataforma (Settings + automacao + wizard conversacional).
        _cs = (content_str or "").strip()
        if _cs.startswith('```'):
            _parts = _cs.split('```')
            _cs = _parts[1] if len(_parts) > 1 else ""
            if _cs.lstrip().lower().startswith("json"):
                _cs = _cs.lstrip()[4:]
            _cs = _cs.strip()
        data = json.loads(_cs)
        
        # Converter para Competency objects
        technical = [
            Competency(
                name=comp["name"],
                type="technical",
                weight=comp["weight"],
                seniority_level=seniority,
                is_critical=comp.get("is_critical", False)
            )
            for comp in data["technical_competencies"]
        ]
        
        behavioral = [
            Competency(
                name=comp["name"],
                type="behavioral",
                weight=comp["weight"],
                seniority_level=seniority,
                is_critical=False
            )
            for comp in data.get("behavioral_competencies", [])
        ]
        
        cultural = [
            Competency(
                name=comp["name"],
                type="cultural",
                weight=comp["weight"],
                seniority_level=seniority,
                is_critical=False
            )
            for comp in data.get("cultural_competencies", [])
        ]
        
        return CompetencySuggestion(
            technical_competencies=technical,
            behavioral_competencies=behavioral,
            cultural_competencies=cultural,
            suggested_weights={comp.name: comp.weight for comp in technical + behavioral + cultural},
            confidence_score=data.get("confidence_score", 0.9)
        )
    
    async def generate_screening_questions(
        self,
        competencies: list[Competency],
        mode: Literal["compact", "full"] = "compact",
        job_description: str | None = None,
        seniority: str | None = None,
        enriched_jd: dict | None = None,
        collect_dropped: list | None = None,
        precomputed_selected_traits: list | None = None,
    ) -> list[WSIQuestion]:
        """
        ETAPA 2: Gera perguntas científicas baseadas em competências.

        Aplica frameworks:
        - CBI para perguntas contextuais (técnico E comportamental)
        - Dreyfus para autodeclaração de proficiência técnica
        - Bloom para microcases situacionais
        - Big Five para fit comportamental/cultural (F6.6 via pipeline F2.5→F3→F5)

        Args:
            competencies: Lista de competências a avaliar
            mode: "compact" (7 perguntas) ou "full" (12 perguntas)
            job_description: Descrição da vaga para pipeline F2.5 OCEAN scoring (opcional)
            seniority: Nível de senioridade para seleção F5 top-N traits (opcional)
            enriched_jd: Output serializado de JdEnrichmentService (opcional).
                         Quando fornecido: preenche big_five_mapping das competências
                         comportamentais e usa about_role+responsabilidades como
                         contexto F2.5 se job_description não fornecido.

        Returns:
            Lista de perguntas WSI estruturadas
        """
        # F1.C → WSI bridge: enriquecer competências com big_five_mapping do enriched_jd
        if enriched_jd:
            enriched_comps, jd_context = self._build_competencies_from_enriched_jd(
                enriched_jd, seniority or "pleno"
            )
            competencies = self._merge_with_enriched(competencies, enriched_comps)
            if not job_description and jd_context:
                job_description = jd_context
                logger.info("WSI F1.C bridge: usando jd_context do enriched_jd para F2.5")

        # FairnessGuard pre-check (Fase 2.3) — nao chama LLM se JD enviesado
        _pre = _wsi_fairness_check(job_description or "")
        if _pre is not None and _pre.is_blocked:
            logger.warning(
                "[WSIService] FairnessGuard PRE-BLOCK: category=%s — skipping LLM",
                _pre.category,
            )
            return []

        questions = await self.question_generator.generate_all(
            competencies,
            mode,
            job_description=job_description,
            seniority=seniority,
            precomputed_selected_traits=precomputed_selected_traits,
        )
        # Layer 4: fairness scan por-pergunta (drop + audit)
        return self._apply_fairness_l4(questions, collect_dropped=collect_dropped)

    async def generate_from_simple_inputs(
        self,
        skills: list[str],
        behavioral: list[str] | None = None,
        seniority: str = "pleno",
        job_description: str | None = None,
        mode: Literal["compact", "full"] = "compact",
        max_questions: int | None = None,
        collect_dropped: list | None = None,
        precomputed_selected_traits: list | None = None,
    ) -> list[WSIQuestion]:
        """Convenience wrapper: converts string skill/behavioral lists into Competency
        objects and delegates to ``generate_screening_questions()``.

        This allows callers that only have simple string lists (e.g. API
        endpoints, wizard) to use the canonical F6 pipeline without manually
        building ``Competency`` objects.
        """
        _seniority = (seniority or "pleno").lower().strip()
        _seniority_level = _seniority.replace(" ", "_").replace("-", "_")
        _valid_levels = ("junior", "pleno", "senior", "lead", "executive", "estagiario", "principal", "diretor", "vp_clevel")
        if _seniority_level not in _valid_levels:
            _seniority_level = "pleno"

        competencies: list[Competency] = []

        for idx, skill in enumerate(skills or []):
            if not skill or not skill.strip():
                continue
            competencies.append(Competency(
                name=skill.strip(),
                type="technical",
                weight=round(max(0.1, 1.0 - idx * 0.05), 2),
                seniority_level=_seniority_level if _seniority_level in ("junior", "pleno", "senior", "lead", "executive") else "pleno",
                is_critical=idx < 3,
            ))

        for idx, comp in enumerate(behavioral or []):
            if not comp or not comp.strip():
                continue
            competencies.append(Competency(
                name=comp.strip(),
                type="behavioral",
                weight=round(max(0.1, 0.9 - idx * 0.05), 2),
                seniority_level=_seniority_level if _seniority_level in ("junior", "pleno", "senior", "lead", "executive") else "pleno",
                is_critical=False,
            ))

        if not competencies:
            competencies.append(Competency(
                name="General",
                type="technical",
                weight=1.0,
                seniority_level="pleno",
                is_critical=False,
            ))

        questions = await self.generate_screening_questions(
            competencies=competencies,
            mode=mode,
            job_description=job_description,
            seniority=_seniority_level if _seniority_level in ("junior", "pleno", "senior", "lead", "executive") else "pleno",
            collect_dropped=collect_dropped,
            precomputed_selected_traits=precomputed_selected_traits,
        )
        if max_questions is not None and len(questions) > max_questions:
            questions = questions[:max_questions]
        return questions

    async def generate_wsi_package(
        self,
        *,
        skills: list[str],
        behavioral: list[str] | None = None,
        seniority: str = "pleno",
        job_description: str | None = None,
        mode: Literal["compact", "full"] = "compact",
        dept_blend=None,
        collect_dropped: list | None = None,
    ) -> dict[str, Any]:
        """Orquestracao canonica unica WSI (Consolidacao Fase 2.4b).

        Produz perguntas + Big Five (profile + trait_rankings F3 rico) num so
        lugar, extraindo OCEAN UMA vez (sem dupla chamada LLM). Reusada pelo
        wizard conversacional (bulk). Settings pode continuar usando
        generate_from_simple_inputs direto.

        dept_blend (Optional[BigFiveBlend], ADR-LGPD-001): quando fornecido,
        rank_traits usa a formula 3/4-camadas; senao, llm_only (paridade com o
        bigfive_node atual do wizard).

        Returns dict: {questions: list[WSIQuestion], bigfive_profile: dict|None,
        trait_rankings: list[dict], dropped: list}.
        """
        from .bigfive import rank_traits as _rank_traits, TRAITS as _TRAITS

        _sen = (seniority or "pleno").lower().strip().replace(" ", "_").replace("-", "_")

        behav_list = [b for b in (behavioral or []) if b and b.strip()]

        selected_traits: list = []
        trait_rankings: list[dict] = []
        bigfive_profile: dict[str, Any] = {}
        if job_description:
            # F2.5 — extracao OCEAN UMA vez (reusada p/ perguntas + painel).
            ranked = await self.question_generator._extract_ocean_scores(
                job_description, behav_list
            )
            selected_traits = self.question_generator._select_traits_by_seniority(
                ranked, _sen
            )
            # 0-100 -> 0-1 (escala do rank_traits canonico).
            llm_scores = {t.trait: round(t.score / 100.0, 4) for t in ranked}
            trait_rankings = _rank_traits(llm_scores, _sen, dept_blend=dept_blend)
            bigfive_profile = {t: llm_scores.get(t, 0.5) for t in _TRAITS}
            bigfive_profile["evidences"] = {t.trait: list(t.evidence or []) for t in ranked}

        # Perguntas — reusa traits pre-computados (sem 2a extracao OCEAN quando
        # job_description presente).
        questions = await self.generate_from_simple_inputs(
            skills=skills,
            behavioral=behav_list,
            seniority=seniority,
            job_description=job_description,
            mode=mode,
            collect_dropped=collect_dropped,
            precomputed_selected_traits=(selected_traits if job_description else None),
        )
        return {
            "questions": questions,
            "bigfive_profile": bigfive_profile or None,
            "trait_rankings": trait_rankings,
            "dropped": collect_dropped or [],
        }

    async def suggest_single_question(
        self,
        *,
        prompt: str,
        block_id: int | None = None,
        job_title: str | None = None,
        seniority: str | None = None,
        technical_skills: list[str] | None = None,
        behavioral_competencies: list[str] | None = None,
    ) -> dict[str, Any]:
        """Gera UMA pergunta de triagem a partir de instrução do recrutador (cirúrgica).

        Consolidação WSI Fase 2 (2026-05-31): extraído do endpoint
        /api/v1/wsi/suggest-question para ser o ÚNICO canônico — reusado por
        Settings (endpoint) E pelo HITL do wizard conversacional (add/edit
        pergunta). Single source of truth. Usa o LLM canônico do serviço
        (self.llm.safe_invoke, provider=claude) + safe_json_parse (robusto a
        cercas markdown).
        """
        block_context = {
            2: "Bloco 2 - Elegibilidade: perguntas eliminatórias sobre disponibilidade, requisitos mínimos",
            3: "Bloco 3 - Técnica: perguntas sobre conhecimento técnico, experiência prática",
            4: "Bloco 4 - Situacional/Comportamental: perguntas sobre soft skills, liderança, trabalho em equipe",
        }
        block_info = block_context.get(block_id, "Bloco genérico")
        # FairnessGuard pre-check (Fase 2.3): recusa instrucao discriminatoria
        # ANTES de chamar o LLM (mesmo guard do bulk + Settings).
        _pre = _wsi_fairness_check(prompt)
        if _pre is not None and _pre.is_blocked:
            logger.warning(
                "[WSIService] suggest_single_question PRE-BLOCK: category=%s",
                _pre.category,
            )
            return {
                "success": False,
                "error": (
                    "Essa instrucao contem criterio potencialmente discriminatorio "
                    "e nao pode gerar pergunta de triagem. Reformule focando em "
                    "competencias e comportamentos observaveis."
                ),
                "blocked_category": _pre.category,
            }
        full_prompt = f"""Você é um especialista em recrutamento usando a metodologia WSI.
O recrutador pediu para criar uma pergunta de triagem com base nesta instrução:

INSTRUÇÃO DO RECRUTADOR: "{prompt}"

CONTEXTO:
- Vaga: {job_title or 'Não especificada'}
- Senioridade: {seniority or 'Não especificada'}
- {block_info}
- Skills técnicas da vaga: {', '.join(technical_skills or []) or 'Não especificadas'}
- Competências comportamentais: {', '.join(behavioral_competencies or []) or 'Não especificadas'}

REGRAS:
1. Crie UMA pergunta profissional e bem formulada em português brasileiro
2. Se a instrução menciona "eliminatória", "disponibilidade" ou requisito obrigatório, marque como eliminatory
3. Se a instrução menciona skills técnicas, marque como technical
4. Senão, marque como classificatory/behavioral
5. A pergunta deve ser clara, direta e adequada para triagem de candidatos

Retorne APENAS JSON válido:
{{
  "question": "Texto completo da pergunta em português",
  "type": "eliminatory|classificatory",
  "category": "eligibility|technical|behavioral",
  "block_id": {block_id or 3},
  "skill_targeted": "competência que a pergunta avalia",
  "bloom_level": 3
}}"""
        try:
            content = await self.llm.safe_invoke(full_prompt, provider="claude")
            data = safe_json_parse(content, fallback={})
        except Exception as exc:  # noqa: BLE001 — fail-loud (nunca silent)
            logger.error("[WSIService] suggest_single_question failed: %s", exc)
            return {"success": False, "error": "Não foi possível gerar a sugestão. Tente novamente."}
        if data.get("question"):
            # Layer 4 fairness scan na pergunta gerada (fail-loud, nunca silent)
            _post = _wsi_fairness_check(data["question"])
            if _post is not None and _post.is_blocked:
                logger.warning(
                    "[WSIService] suggest_single_question L4 BLOCK: category=%s",
                    _post.category,
                )
                return {
                    "success": False,
                    "error": (
                        "A pergunta gerada foi bloqueada pelo filtro de equidade. "
                        "Tente reformular a instrucao."
                    ),
                    "blocked_category": _post.category,
                }
            return {
                "success": True,
                "question": data["question"],
                "type": data.get("type", "classificatory"),
                "category": data.get("category", "technical"),
                "block_id": data.get("block_id", block_id or 3),
                "skill_targeted": data.get("skill_targeted", ""),
                "bloom_level": data.get("bloom_level", 3),
            }
        return {"success": False, "error": "Não foi possível gerar a sugestão. Tente novamente."}

    def _apply_fairness_l4(
        self, questions: list[WSIQuestion], collect_dropped: list | None = None
    ) -> list[WSIQuestion]:
        """Layer-4 fairness scan por-pergunta (Fase 2.3, portado do fork).

        Descarta perguntas enviesadas (FairnessGuard.check.is_blocked), registra
        em collect_dropped (audit trail) e loga. Fail-open por chamada via
        _wsi_fairness_check. Enforca compliance NO PRODUTOR (canonico) — Settings
        E wizard herdam o filtro automaticamente.
        """
        kept: list[WSIQuestion] = []
        for q in questions:
            text = getattr(q, "question_text", "") or ""
            res = _wsi_fairness_check(text)
            if res is not None and res.is_blocked:
                logger.warning(
                    "[WSIService] FairnessGuard L4 dropped question: category=%s terms=%s",
                    res.category, res.blocked_terms,
                )
                if collect_dropped is not None:
                    collect_dropped.append({
                        "question": text,
                        "category": res.category,
                        "blocked_terms": res.blocked_terms,
                        "message": res.educational_message,
                    })
            else:
                kept.append(q)
        return kept

    @staticmethod
    def _build_competencies_from_enriched_jd(
        enriched_jd: dict,
        seniority: str = "pleno",
    ) -> tuple:
        """F1.C → WSI bridge: converte EnrichedJobDescription em competências WSI.

        Extrai de enriched_jd:
        - skills_obrigatorias → Competency(type="technical") com is_critical nos top 3
        - competencias_comportamentais → Competency(type="behavioral") com big_five_mapping preenchido
        - about_role + responsabilidades → texto de contexto para F2.5

        Args:
            enriched_jd: dict output de JdEnrichmentService (EnrichedJobDescription serializado)
            seniority: nível para seniority_level das competências geradas

        Returns:
            Tuple[List[Competency], str] — (competências com big_five_mapping, jd_context para F2.5)
        """
        _SENIORITY_MAP = {
            "estagiario": "junior", "estagiário": "junior",
            "junior": "junior", "júnior": "junior",
            "pleno": "pleno",
            "senior": "senior", "sênior": "senior",
            "lead": "lead", "principal": "lead",
            "diretor": "executive", "vp": "executive", "clevel": "executive", "c-level": "executive",
        }
        seniority_level = _SENIORITY_MAP.get(seniority.lower().strip(), "pleno")
        competencies: list = []

        # --- Técnicas: de skills_obrigatorias ---
        skills_raw = enriched_jd.get("skills_obrigatorias", [])
        n_skills = max(len(skills_raw), 1)
        for i, skill_entry in enumerate(skills_raw):
            if isinstance(skill_entry, str):
                skill_name = skill_entry
            elif isinstance(skill_entry, dict):
                skill_name = skill_entry.get("skill") or skill_entry.get("value") or str(skill_entry)
            else:
                continue
            competencies.append(Competency(
                name=skill_name,
                type="technical",
                weight=round(0.6 / n_skills, 4),
                seniority_level=seniority_level,
                is_critical=(i < 2),  # F6-5: máximo 2 skills críticas por triagem (spec §6.5)
            ))

        # --- Comportamentais: de competencias_comportamentais com trait pré-mapeado ---
        behavioral_raw = enriched_jd.get("competencias_comportamentais", [])
        n_behavioral = max(len(behavioral_raw), 1)
        for comp_entry in behavioral_raw:
            if isinstance(comp_entry, str):
                comp_name, trait = comp_entry, None
            elif isinstance(comp_entry, dict):
                comp_name = (
                    comp_entry.get("competencia")
                    or comp_entry.get("value")
                    or comp_entry.get("name")
                    or str(comp_entry)
                )
                # trait_big_five ou big_five_mapping — aceitar ambos
                trait = comp_entry.get("trait_big_five") or comp_entry.get("big_five_mapping")
            else:
                continue
            competencies.append(Competency(
                name=comp_name,
                type="behavioral",
                weight=round(0.4 / n_behavioral, 4),
                seniority_level=seniority_level,
                big_five_mapping=trait,
            ))

        # --- Texto de contexto para F2.5 ---
        about = enriched_jd.get("about_role", "")
        resps = enriched_jd.get("responsabilidades", [])
        if isinstance(resps, list):
            resps_text = " ".join(resps)
        else:
            resps_text = str(resps)
        jd_context = f"{about}\n\n{resps_text}".strip()

        return competencies, jd_context

    @staticmethod
    def _merge_with_enriched(
        original: list["Competency"],
        enriched: list["Competency"],
    ) -> list["Competency"]:
        """Mescla lista original de competências com versão enriquecida.

        Para cada competência original sem big_five_mapping, tenta encontrar
        correspondência por nome (case-insensitive) na lista enriquecida e
        copia o big_five_mapping. Mantém todas as competências originais.
        """
        enriched_by_name = {c.name.lower().strip(): c for c in enriched}
        merged = []
        for comp in original:
            if comp.big_five_mapping is None and comp.type in ("behavioral", "cultural"):
                match = enriched_by_name.get(comp.name.lower().strip())
                if match and match.big_five_mapping:
                    comp = comp.model_copy(update={"big_five_mapping": match.big_five_mapping})
            merged.append(comp)
        # Adicionar comportamentais enriquecidas sem equivalente original
        original_names = {c.name.lower().strip() for c in original}
        for comp in enriched:
            if comp.name.lower().strip() not in original_names:
                merged.append(comp)
        return merged

    async def analyze_response(
        self,
        question: WSIQuestion,
        response: str
    ) -> ResponseAnalysis:
        """
        ETAPA 3: Analisa resposta e atribui score 1-5.
        
        Aplica:
        - Extração de autodeclaração (se houver)
        - Análise de contexto (Bloom + Dreyfus)
        - Detecção de evidências concretas
        - Detecção de red flags
        - Cálculo de score ponderado
        
        Args:
            question: Pergunta WSI
            response: Resposta do candidato (texto ou transcrição)
            
        Returns:
            ResponseAnalysis com scores e justificativas
        """
        return await self.response_analyzer.analyze(question, response)
    
    def calculate_wsi(
        self,
        candidate_id: str,
        job_vacancy_id: str,
        responses: list[ResponseAnalysis],
        weights: dict[str, float]
    ) -> WSIResult:
        """
        ETAPA 4: Calcula WSI final.
        
        Fórmula: WSI = Σ(peso_i × score_i) / 100
        
        Classificação:
        - 4.5-5.0: Excelente
        - 4.0-4.4: Alto
        - 3.0-3.9: Médio
        - 2.0-2.9: Regular
        - < 2.0: Baixo
        
        Args:
            candidate_id: ID do candidato
            job_vacancy_id: ID da vaga
            responses: Lista de análises de respostas
            weights: Pesos por competência
            
        Returns:
            WSIResult com score final e classificação
        """
        # Normalize weights before calculation
        normalized_weights = normalize_weights(weights)
        
        return self.score_calculator.calculate(
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            responses=responses,
            weights=normalized_weights
        )
    
    async def generate_structured_report(
        self,
        candidate_id: str,
        wsi_result: WSIResult,
        responses: list[ResponseAnalysis]
    ) -> StructuredReport:
        """
        ETAPA 5: Gera parecer estruturado.
        
        Inclui:
        - Sumário executivo
        - Análise técnica (pontos fortes, gaps)
        - Análise comportamental
        - Fit cultural
        - Recomendação fundamentada (APROVADO/AGUARDANDO/NÃO APROVADO)
        
        Args:
            candidate_id: ID do candidato
            wsi_result: Resultado WSI calculado
            responses: Análises detalhadas
            
        Returns:
            StructuredReport com parecer completo
        """
        return await self.report_generator.generate_report(
            candidate_id, wsi_result, responses
        )
    
    async def generate_candidate_feedback(
        self,
        wsi_result: WSIResult,
        responses: list[ResponseAnalysis],
        decision: Literal["aprovado", "aguardando", "nao_aprovado"]
    ) -> CandidateFeedback:
        """
        ETAPA 6: Gera feedback estruturado para candidato.
        
        Inclui:
        - Mensagem principal
        - Pontos fortes técnicos
        - Oportunidades de desenvolvimento
        - Próximos passos ou plano de desenvolvimento
        - Recursos recomendados (se não aprovado)
        
        Args:
            wsi_result: Resultado WSI
            responses: Análises detalhadas
            decision: Decisão final
            
        Returns:
            CandidateFeedback estruturado e construtivo
        """
        return await self.report_generator.generate_feedback(
            wsi_result, responses, decision
        )



wsi_service = WSIService()


async def generate_wsi_questions_tool(job_id: str, count: int = 5, **kwargs) -> list[dict[str, Any]]:
    result = await wsi_service.generate_from_simple_inputs(
        skills=kwargs.get("technical_skills", []),
        behavioral=kwargs.get("behavioral_competencies"),
        seniority=kwargs.get("seniority", "pleno"),
        job_description=kwargs.get("job_description"),
        max_questions=count,
    )
    return [q.dict() if hasattr(q, "dict") else q for q in result]


def get_wsi_service() -> "WSIService":
    """Return the module-level WSIService singleton. No db needed — pure LLM service."""
    return wsi_service

