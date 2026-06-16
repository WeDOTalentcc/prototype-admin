from __future__ import annotations

from app.domains.base import DomainAction

CV_SCREENING_ACTIONS: list[DomainAction] = [
    DomainAction(action_id="parse_cv", name="Analisar CV", description="Analisar e extrair dados estruturados do CV"),
    DomainAction(action_id="auto_screen", name="Triagem automática", description="Triagem automática contra requisitos da vaga"),
    DomainAction(action_id="batch_screen", name="Triagem em lote", description="Triagem em lote de múltiplos candidatos"),
    DomainAction(action_id="calculate_wsi_score", name="Calcular WSI", description="Calcular score WSI baseado no CV"),
    DomainAction(action_id="rank_candidates", name="Rankear candidatos", description="Rankear candidatos por score WSI"),
    DomainAction(action_id="dynamic_cutoff", name="Corte dinâmico", description="Aplicar corte dinâmico (top 25%)"),
    DomainAction(action_id="detect_red_flags", name="Detectar red flags", description="Detectar red flags no CV"),
    DomainAction(action_id="check_saturation", name="Verificar saturação", description="Verificar saturação do pipeline"),
    DomainAction(action_id="classify_bloom", name="Classificar Bloom", description="Classificar respostas pela Taxonomia de Bloom"),
    DomainAction(action_id="classify_dreyfus", name="Classificar Dreyfus", description="Classificar nível de proficiência Dreyfus"),
    DomainAction(action_id="map_big_five", name="Mapear Big Five", description="Mapear traços Big Five comportamentais"),
    DomainAction(action_id="validate_cbi", name="Validar CBI", description="Validar respostas contra framework CBI"),
    DomainAction(action_id="generate_report", name="Gerar parecer", description="Gerar parecer completo do candidato"),
    DomainAction(action_id="compare_candidates", name="Comparar candidatos", description="Comparar candidatos lado a lado"),
    DomainAction(action_id="calibrate_model", name="Calibrar modelo", description="Calibrar modelo com feedback do recrutador"),
    DomainAction(action_id="explain_score", name="Explicar score", description="Explicar detalhadamente como o score foi calculado"),
    DomainAction(action_id="evaluate_rubric", name="Avaliar rubrica", description="Avaliar candidato por rubrica estruturada"),
    DomainAction(action_id="generate_questions", name="Gerar perguntas", description="Gerar perguntas de triagem WSI"),
    DomainAction(action_id="adjust_questions", name="Ajustar perguntas", description="Ajustar/refinar perguntas com IA"),
    DomainAction(action_id="voice_screening", name="Triagem por voz", description="Triagem por voz com WSI"),
    DomainAction(action_id="normalize_scores", name="Normalizar scores", description="Normalizar scores entre candidatos"),
    DomainAction(action_id="assess_seniority", name="Avaliar senioridade", description="Avaliar nível de senioridade"),
    DomainAction(action_id="send_feedback", name="Enviar feedback", description="Enviar feedback personalizado ao candidato"),
    DomainAction(action_id="pre_qualify", name="Pré-qualificar", description="Pré-qualificar candidato antes da triagem"),
]
