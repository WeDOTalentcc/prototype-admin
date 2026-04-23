# frozen_string_literal: true

module Evaluations
  class AiFeedbackService
    WSI_SCALE_MAX = 10.0
    WSI_AUTO_APPROVAL_MIN = 7.5
    WSI_REVIEW_BAND_MIN = 6.0

    SUMMARY_JSON_PLACEHOLDER =
      "Candidata excepcional com domínio completo de arquitetura, desenvolvimento full stack e liderança técnica. " \
      "Demonstra capacidade de tomar decisões fundamentadas em métricas, resolver problemas complexos sistematicamente e liderar times com impacto mensurável. " \
      "Altamente recomendada para posições de liderança técnica sênior."

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
      @request_id = SecureRandom.uuid
    end

    def self.call(evaluation_candidate:, **opts)
      new(evaluation_candidate: evaluation_candidate, **opts).call
    end

    def call
      start_time = Time.current

      payload = build_payload
      deterministic = build_deterministic_analysis(payload)

      validate_payload!(payload)

      analysis = generate_analysis(payload, deterministic: deterministic)
      weaknesses = weaknesses_with_gap_severity(analysis[:weaknesses], @evaluation_candidate)

      processing_time_ms = ((Time.current - start_time) * 1000).to_i

      result = {
        status: "success",
        candidate_id: @evaluation_candidate.candidate_id,
        candidate_name: payload[:candidate_name],
        evaluation_id: @evaluation_candidate.evaluation_id,
        wsi_macro_distribution: WsiDimensionScores.new(evaluation_candidate: @evaluation_candidate).macro_distribution_weights,
        wsi_score: deterministic[:wsi_score],
        wsi_classification: deterministic[:wsi_classification],
        wsi_level: deterministic[:wsi_level],
        dreyfus_level: deterministic[:dreyfus_level],
        skills_analysis: analysis[:skills_analysis],
        behavioral_analysis: analysis[:behavioral_analysis],
        approval_criteria: analysis[:approval_criteria],
        full_analysis: analysis[:full_analysis],
        summary: analysis[:summary],
        strengths: analysis[:strengths],
        weaknesses: weaknesses,
        recommendation: analysis[:recommendation],
        recommendation_justification: analysis[:recommendation_justification],
        next_steps: analysis[:next_steps],
        processing_time_ms: processing_time_ms,
        request_id: @request_id,
        methodology: "WSI (WeDoTalent Skill Index)"
      }
      result
    rescue StandardError => e
      Rails.logger.error "[AiFeedbackService] Error: #{e.class} - #{e.message} - request_id: #{@request_id}, backtrace: #{e.backtrace.first(5).join(' | ')}"
      raise
    end

    private

    def build_payload
      candidate = @evaluation_candidate.candidate
      job = @evaluation_candidate.job
      evaluation = @evaluation_candidate.evaluation

      candidate_name = candidate.name.presence || candidate.email.presence || "Candidate ##{candidate.id}"
      job_title = job.title.presence || "Job ##{job.id}"
      curriculum_text = candidate.curriculum_text.to_s

      answers = Answer.where(
        evaluation_id: @evaluation_candidate.evaluation_id,
        candidate_id: @evaluation_candidate.candidate_id
      ).includes(:question)

      formatted_answers = answers.map do |answer|
        question = answer.question
        comments = parse_comments_response(answer.comments_response)

        {
          id: answer.id,
          title: question&.title,
          description: answer.description,
          comments_response: comments,
          analysis_data: answer.analysis_data,
          final_skill_score: answer.final_skill_score,
          competence_type: question&.competence_type,
          bloom_level: question&.bloom_level,
          dreyfus_target: question&.dreyfus_target,
          ocean_trait: question&.ocean_trait
        }
      end

      {
        candidate_name: candidate_name,
        candidate_id: candidate.id,
        job_title: job_title,
        job_id: job.id,
        evaluation_id: evaluation.id,
        curriculum_text: curriculum_text,
        answers: formatted_answers
      }
    end

    def parse_comments_response(comments_str)
      return {} if comments_str.blank?

      return comments_str if comments_str.is_a?(Hash)

      if comments_str.to_s.strip.start_with?("{")
        normalized = comments_str.to_s
          .gsub(/(\w+):\s*/, '"\1": ')
          .gsub(/:\s*([a-zA-Z]\w+)(?=[\s,}])/, ': "\1"')

        begin
          parsed = JSON.parse(normalized)
          return parsed
        rescue JSON::ParserError => e
          begin
            parsed = JSON.parse(comments_str.to_s)
            return parsed
          rescue JSON::ParserError
            Rails.logger.debug "[AiFeedbackService] JSON parse failed, using regex fallback"
          end
        end
      end

      result = {}
      content = comments_str.to_s.strip
      content = content.gsub(/^\{|\}$/, "").strip

      if content.match(/score:\s*([0-9.]+)/)
        result["score"] = $1.to_f
      end

      if content.match(/is_answer_satisfactory:\s*(true|false)/i)
        result["is_answer_satisfactory"] = $1.downcase == "true"
      end

      if content.match(/feedback_for_recruiter:\s*"([^"]+)"/)
        result["feedback_for_recruiter"] = $1.strip
      elsif content.match(/feedback_for_recruiter:\s*([^,}]+?)(?=,\s*\w+:|$|\})/)
        result["feedback_for_recruiter"] = $1.strip
      end

      result
    rescue => e
      Rails.logger.warn "[AiFeedbackService] Error parsing comments_response: #{e.message} - comments: #{comments_str.to_s[0..100]}"
      {}
    end

    def validate_payload!(payload)
      raise ArgumentError, "candidate_name é obrigatório" if payload[:candidate_name].blank?
      raise ArgumentError, "job_title é obrigatório" if payload[:job_title].blank?
      raise ArgumentError, "answers deve ser uma lista não-vazia" if payload[:answers].blank? || !payload[:answers].is_a?(Array)
    end

    def weaknesses_with_gap_severity(llm_weaknesses, evaluation_candidate)
      gap_result = Wsi::GapAnalyzer.call(evaluation_candidate: evaluation_candidate)
      gaps = gap_result[:gaps]
      llm = Array(llm_weaknesses).map { |w| w.is_a?(Hash) ? (w["text"] || w[:text]).to_s : w.to_s }

      if gaps.blank?
        return llm.map { |text| { "text" => text, "severity" => nil } }
      end

      gaps.each_with_index.map do |g, i|
        {
          "text" => llm[i].presence || g.label.to_s,
          "severity" => g.severidade.to_s.upcase
        }
      end
    end

    def build_prompt(payload, deterministic:)
      candidate_name = payload[:candidate_name]
      job_title = payload[:job_title]
      curriculum = payload[:curriculum_text] || ""
      answers = payload[:answers] || []
      wsi_score = deterministic[:wsi_score]
      wsi_classification = deterministic[:wsi_classification]
      wsi_level = deterministic[:wsi_level]
      dreyfus_level = deterministic[:dreyfus_level]
      answers_section = ""
      total_score = 0
      count_scores = 0

      answers.each_with_index do |answer, i|
        title = answer[:title] || "Question #{i + 1}"
        description = answer[:description] || "No answer provided"
        comments = answer[:comments_response] || {}

        score = comments["score"] || comments[:score] || 0
        if score.is_a?(Numeric)
          total_score += score
          count_scores += 1
        end

        is_satisfactory = comments["is_answer_satisfactory"] || comments[:is_answer_satisfactory] || false
        feedback = comments["feedback_for_recruiter"] || comments[:feedback_for_recruiter] || ""

        competence_type = answer[:competence_type] || "N/A"
        bloom_level = answer[:bloom_level] || "N/A"
        dreyfus_target = answer[:dreyfus_target] || "N/A"
        ocean_trait = answer[:ocean_trait] || "N/A"

        status_emoji = is_satisfactory ? "✅" : "⚠️"

        answers_section += <<~TEXT

          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          QUESTÃO #{i + 1}: #{title}
          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

          🎯 WSI METADATA:
          - Tipo de Competência: #{competence_type}
          - Nível Bloom Esperado: #{bloom_level}
          - Nível Dreyfus Target: #{dreyfus_target}
          - Traço OCEAN: #{ocean_trait}

          📝 RESPOSTA DO CANDIDATO:

          #{description[0..800]}#{'...' if description.length > 800}


          #{status_emoji} AVALIAÇÃO: Score #{score}/1.0 | #{is_satisfactory ? 'Satisfatória' : 'Necessita revisão'}


          💡 FEEDBACK DO AVALIADOR:

          #{feedback}


        TEXT
      end

      <<~PROMPT
        You are a senior technical recruiter and evaluation specialist following the WSI (WeDoTalent Skill Index) methodology.

        ════════════════════════════════════════════════════════════════════
        WSI METHODOLOGY REFERENCE
        ════════════════════════════════════════════════════════════════════

        The WSI methodology integrates 4 scientific frameworks:

        1. CBI (Competency-Based Interviewing) - McClelland, 1973
        2. Bloom's Taxonomy (Revised) - Cognitive levels 1-5
        3. Dreyfus Model - Maturity scale 1-5:
           - 1: Novice (theoretical knowledge only)
           - 2: Advanced Beginner (partial guided application)
           - 3: Competent (stable, consistent execution)
           - 4: Proficient (autonomous, adaptive)
           - 5: Expert (intuitive, contextual mastery)
        4. Big Five (OCEAN Model) - Behavioral assessment

        WSI Score Formula per Skill (same as deterministic scorer — Fase 8):
        Technical: (0.35 × Self-Declaration_norm) + (0.40 × Context/Evidence_norm) + (0.25 × Bloom_alignment) — scaled to 0-10, then structural adjustments.
        Behavioral: (0.35 × STAR_structure) + (0.40 × Trait_signals) + (0.25 × Bloom_alignment) — scaled to 0-10, then structural adjustments.

        Penalties:
        - Score inflation (declares high, poor context): -1.0 to -1.5
        - Generic response (no specific projects/metrics): -0.5
        - Lack of context (less than 2 STAR evidences): -0.3
        - Appears copied (official documentation text): -1.0

        Bonuses:
        - Humility (declares low, high context): +0.5
        - Exceptional evidence (open source, quantified metrics): +0.3

        WSI Final classification (methodology doc §9.5, scale 0-10):
        - 9.0-10.0: Exceptional
        - 8.0-8.9: Excellent
        - 7.0-7.9: High
        - 6.0-6.9: Medium
        - 4.5-5.9: Below average
        - 0.0-4.4: Regular

        ════════════════════════════════════════════════════════════════════
        EVALUATION DATA
        ════════════════════════════════════════════════════════════════════


        👤 CANDIDATE: #{candidate_name}
        💼 POSITION: #{job_title}
        📊 WSI SCORE (CALCULADO - USE ESTE VALOR): #{wsi_score}/#{WSI_SCALE_MAX.to_i}
        📋 WSI CLASSIFICATION (USE ESTA): #{wsi_classification}
        📐 WSI LEVEL (USE ESTE): #{wsi_level}
        🎯 DREYFUS LEVEL: #{dreyfus_level}
        📈 TOTAL QUESTIONS: #{answers.length}

        #{curriculum.present? ? "📄 RESUME:\n#{curriculum[0..1000]}" : "Resume not provided"}

        ⚠️ IMPORTANT: Per-question scores in comments below are normalized 0.0-1.0.#{' '}
        Multiply by 10 to express each item on the same 0-10 scale as final_skill_score (e.g. 0.82 → 8.2).
        The OVERALL WSI SCORE above is already the final 0-10 aggregate — use it as-is.

        ════════════════════════════════════════════════════════════════════
        RESPONSES AND EVALUATIONS
        ════════════════════════════════════════════════════════════════════
        #{answers_section}

        ════════════════════════════════════════════════════════════════════
        TASK
        ════════════════════════════════════════════════════════════════════


        Analyze this evaluation following WSI methodology and return a JSON with EXACTLY this structure.
        OBRIGATÓRIO: Use EXATAMENTE os valores WSI fornecidos acima (#{wsi_score}, #{wsi_classification}, #{wsi_level}) em full_analysis e recommendation_justification quando mencionar score ou classificação. O campo summary é um texto narrativo para recrutadores: não use rótulos de metodologia, siglas de frameworks ou fórmulas; o exemplo em "summary" abaixo é só referência de tom e estrutura — escreva um resumo original para ESTE candidato.

        {
          "wsi_score": #{wsi_score},
          "wsi_classification": "#{wsi_classification}",
          "wsi_level": "#{wsi_level}",
          "dreyfus_level": #{dreyfus_level},
        #{'  '}
          "skills_analysis": [
            {
              "skill_name": "Nome da competência avaliada",
              "competence_type": "technical ou behavioral",
              "bloom_level_expected": "Nível Bloom esperado da question",
              "bloom_level_achieved": 4,
              "dreyfus_target": "Nível Dreyfus esperado da question",
              "dreyfus_level_achieved": 4,
              "ocean_trait": "Traço OCEAN relevante da question",
              "self_declaration": 8.0,
              "context_score": 8.5,
              "final_score": 8.2,
              "penalty": 0.0,
              "bonus": 0.3,
              "evidence_type": "Autodeclaração + Contexto",
              "star_evidences": ["Situação específica 1", "Resultado mensurável 2"],
              "red_flags": [],
              "feedback": "Análise específica desta competência"
            }
          ],
        #{'  '}
          "behavioral_analysis": {
            "communication": "Análise da clareza e estrutura das respostas",
            "consistency": "Coerência entre autodeclaração e evidências",
            "depth": "Profundidade técnica demonstrada",
            "ocean_traits": {
              "openness": "Curiosidade e inovação identificada",
              "conscientiousness": "Organização e foco em resultados",
              "extraversion": "Comunicação e assertividade",
              "agreeableness": "Colaboração e empatia",
              "neuroticism": "Controle sob pressão"
            }
          },
        #{'  '}
          "full_analysis": "Análise detalhada de 4-6 parágrafos incluindo: 1) Overview geral do desempenho, 2) Pontos fortes técnicos com exemplos específicos, 3) Áreas de melhoria e gaps identificados, 4) Comparação com requisitos da vaga, 5) Análise comportamental (comunicação, estrutura de resposta), 6) Recomendação final com fundamentação WSI",
        #{'  '}
          "summary": "#{SUMMARY_JSON_PLACEHOLDER}",
        #{'  '}
          "strengths": [
            "Ponto forte específico 1 com evidência da avaliação e classificação Dreyfus",
            "Ponto forte específico 2 com evidência da avaliação e classificação Dreyfus",
            "Ponto forte específico 3 com evidência da avaliação e classificação Dreyfus"
          ],
        #{'  '}
          "weaknesses": [
            "Gap ou área de melhoria 1 com evidência e nível Dreyfus identificado",
            "Gap ou área de melhoria 2 com evidência e nível Dreyfus identificado"
          ],
        #{'  '}
          "recommendation": "APPROVED" or "ADDITIONAL_ANALYSIS" or "NOT_RECOMMENDED",
        #{'  '}
          "recommendation_justification": "Justificativa clara e objetiva da recomendação em 2-3 sentenças, baseada no WSI score e classificação",
        #{'  '}
          "next_steps": "Sugestão específica sobre o que fazer com este candidato (ex: agendar entrevista técnica focada em X, solicitar projeto prático em Y, agradecer participação)",
        #{'  '}
          "approval_criteria": {
            "wsi_threshold": #{WSI_AUTO_APPROVAL_MIN},
            "meets_threshold": #{wsi_score >= WSI_AUTO_APPROVAL_MIN},
            "percentile_rank": "#{wsi_score >= WSI_AUTO_APPROVAL_MIN ? 'Top 25%' : 'Abaixo do esperado'}",
            "auto_approval_eligible": #{wsi_score >= WSI_AUTO_APPROVAL_MIN}
          }
        }

        CRITICAL REQUIREMENTS:
        - summary: 2–4 sentences in Brazilian Portuguese, natural and friendly, as if briefing a hiring manager; weave overall fit, strongest signal, main gap or risk, and what to do next; no methodology names (WSI, Bloom, Dreyfus, OCEAN), no score banners, no bullet labels; must be original for this candidate (do not copy the example string verbatim).
        - MANDATORY: In full_analysis and recommendation_justification, ALWAYS use the exact WSI score (#{wsi_score}), classification (#{wsi_classification}) and level (#{wsi_level}) provided above when citing scores. Do NOT calculate or infer different values.
        - Follow WSI methodology strictly (Dreyfus Model, Bloom's Taxonomy, CBI, Big Five)
        - The scores in comments_response are in 0.0-1.0 scale; multiply by 10 for 0-10 display per question when needed
        - Use the WSI metadata (competence_type, bloom_level, dreyfus_target, ocean_trait) from each question to guide your analysis
        - For per-skill final_score use the persisted 0-10 score from scoring (final_skill_score). The OVERALL wsi_score is already the 0-10 aggregate — use it as-is.
        - Apply penalties for score inflation, generic responses, lack of context
        - Apply bonuses for humility and exceptional evidence
        - Identify STAR evidences (Situation, Task, Action, Result) in responses
        - Classify using Dreyfus levels (1-5) for each skill, comparing achieved level with dreyfus_target
        - Use bloom_level from question to evaluate cognitive level achieved
        - Use ocean_trait to assess behavioral characteristics
        - Detect red flags (copied answers, inconsistencies, lack of depth)
        - Write EVERYTHING in PORTUGUESE (all analysis text, strengths, weaknesses, etc.)
        - Be SPECIFIC citing examples from the responses
        - Be OBJECTIVE and PROFESSIONAL
        - Return ONLY the JSON, no additional text before or after
        - Use double quotes in JSON
        - Do NOT use line breaks inside string values
        - ALL content MUST be written in BRAZILIAN PORTUGUESE language
      PROMPT
    end

    def generate_analysis(payload, deterministic:)
      prompt = build_prompt(payload, deterministic: deterministic)

      start_time = Time.current

      response = Llm::Gateway.chat(
        messages: [
          { role: "user", content: prompt }
        ],
        temperature: 0.3,
        max_tokens: 4000,
        tracking: { operation: "evaluations.ai_feedback" }
      )

      elapsed = Time.current - start_time

      content = response.dig("choices", 0, "message", "content")

      if content.blank?
        Rails.logger.warn "[AiFeedbackService] Gemini returned empty response - request_id: #{@request_id}"
        return fallback_analysis(payload)
      end

      response_text = content.strip
      if response_text.start_with?("```")
        response_text = response_text.split("```")[1]
        response_text = response_text[4..-1] if response_text.start_with?("json")
        response_text = response_text.strip
      end

      parsed = JSON.parse(response_text)

      full_analysis_text = parsed["full_analysis"] || parsed["analise_completa"] || ""

      standardized = {
        wsi_score: deterministic[:wsi_score],
        wsi_classification: deterministic[:wsi_classification],
        wsi_level: deterministic[:wsi_level],
        dreyfus_level: deterministic[:dreyfus_level],
        skills_analysis: deterministic[:skills_analysis],
        behavioral_analysis: deterministic[:behavioral_analysis],
        full_analysis: full_analysis_text,
        summary: resolve_narrative_summary(parsed, full_analysis_text),
        strengths: parsed["strengths"] || parsed["pontos_fortes"] || [],
        weaknesses: parsed["weaknesses"] || parsed["pontos_atencao"] || [],
        recommendation: parsed["recommendation"] || parsed["recomendacao"] || "",
        recommendation_justification: parsed["recommendation_justification"] || parsed["justificativa_recomendacao"] || "",
        next_steps: parsed["next_steps"] || parsed["proximos_passos"] || "",
        approval_criteria: deterministic[:approval_criteria]
      }

      standardized
    rescue JSON::ParserError => e
      response_snippet = defined?(response_text) ? response_text[0..200] : "N/A"
      fallback_analysis(payload, deterministic: deterministic)
    rescue => e
      fallback_analysis(payload, deterministic: deterministic)
    end

    def fallback_analysis(payload, deterministic:)
      return deterministic if deterministic.present?

      answers = payload[:answers] || []
      candidate_name = payload[:candidate_name] || "Candidato"
      job_title = payload[:job_title] || "a vaga"
      total_score = 0
      count_scores = 0
      satisfactory_count = 0

      answers.each do |answer|
        comments = answer[:comments_response] || {}
        score = comments["score"] || comments[:score] || 0
        if score.is_a?(Numeric)
          total_score += score
          count_scores += 1
        end

        if comments["is_answer_satisfactory"] || comments[:is_answer_satisfactory]
          satisfactory_count += 1
        end
      end

      avg_score = count_scores > 0 ? (total_score / count_scores * 10) : 0
      satisfactory_rate = answers.any? ? (satisfactory_count.to_f / answers.length * 100) : 0

      wsi_classification = classify_wsi(avg_score)
      dreyfus_level = infer_dreyfus_from_wsi(avg_score)
      wsi_level = dreyfus_label(dreyfus_level)

      if avg_score >= WSI_AUTO_APPROVAL_MIN && satisfactory_rate >= 70
        recommendation = "APPROVED"
        justification = "WSI Score de #{avg_score.round(2)}/#{WSI_SCALE_MAX.to_i} (#{wsi_classification}) com #{satisfactory_rate.round(0)}% de respostas satisfatórias indica boa adequação à vaga segundo metodologia WSI."
        next_steps = "Agendar entrevista técnica com a equipe para validar experiências práticas e fit cultural."
        auto_approval = true
      elsif avg_score >= WSI_REVIEW_BAND_MIN
        recommendation = "ADDITIONAL_ANALYSIS"
        justification = "WSI Score de #{avg_score.round(2)}/#{WSI_SCALE_MAX.to_i} (#{wsi_classification}) indica potencial mas com lacunas que requerem investigação adicional conforme Modelo Dreyfus."
        next_steps = "Realizar entrevista complementar focada nas áreas de preocupação identificadas antes de prosseguir."
        auto_approval = false
      else
        recommendation = "NOT_RECOMMENDED"
        justification = "WSI Score de #{avg_score.round(2)}/#{WSI_SCALE_MAX.to_i} (#{wsi_classification}) abaixo do esperado para esta posição segundo critérios WSI."
        next_steps = "Agradecer pela participação e manter no banco de talentos para oportunidades futuras mais adequadas ao perfil."
        auto_approval = false
      end

      {
        wsi_score: avg_score.round(2),
        wsi_classification: wsi_classification,
        wsi_level: wsi_level,
        dreyfus_level: dreyfus_level,
        skills_analysis: answers.map.with_index do |answer, i|
          comments = answer[:comments_response] || {}
          score = comments["score"] || comments[:score] || 0
          score_10 = (score.to_f * 10).round(1)
          skill_dreyfus = [ dreyfus_level, (answer[:dreyfus_target] || 3) ].min
          {
            skill_name: answer[:title] || "Questão #{i + 1}",
            competence_type: answer[:competence_type] || "N/A",
            bloom_level_expected: answer[:bloom_level] || "N/A",
            bloom_level_achieved: [ dreyfus_level, 3 ].min,
            dreyfus_target: answer[:dreyfus_target] || "N/A",
            dreyfus_level_achieved: skill_dreyfus,
            ocean_trait: answer[:ocean_trait] || "N/A",
            self_declaration: score_10,
            context_score: score_10,
            final_score: score_10,
            penalty: 0.0,
            bonus: 0.0,
            evidence_type: "Autodeclaração + Contexto",
            star_evidences: [],
            red_flags: [],
            feedback: comments["feedback_for_recruiter"] || comments[:feedback_for_recruiter] || "Análise automática"
          }
        end,
        behavioral_analysis: {
          communication: "Análise comportamental não disponível no modo fallback",
          consistency: "Requer análise detalhada da IA",
          depth: "Baseado apenas em scores numéricos",
          ocean_traits: {
            openness: "N/A",
            conscientiousness: "N/A",
            extraversion: "N/A",
            agreeableness: "N/A",
            neuroticism: "N/A"
          }
        },
        full_analysis: "#{candidate_name} completou a avaliação para a vaga #{job_title} com WSI Score de #{avg_score.round(2)}/#{WSI_SCALE_MAX.to_i}, classificado como #{wsi_classification} (Nível Dreyfus: #{dreyfus_level} - #{wsi_level}). Taxa de respostas satisfatórias: #{satisfactory_rate.round(0)}%. Com base na metodologia WSI, o candidato #{avg_score >= WSI_AUTO_APPROVAL_MIN ? 'demonstra adequação segundo os critérios técnicos e comportamentais' : avg_score < WSI_REVIEW_BAND_MIN ? 'apresenta lacunas significativas em relação aos requisitos' : 'mostra potencial mas requer análise complementar'}. Recomenda-se #{next_steps.downcase}",
        summary: "WSI Score: #{avg_score.round(2)}/#{WSI_SCALE_MAX.to_i} (#{wsi_classification}) | Nível Dreyfus: #{dreyfus_level} (#{wsi_level}) | #{satisfactory_rate.round(0)}% satisfatório | Recomendação: #{recommendation.gsub('_', ' ').titleize}",
        strengths: satisfactory_count > 0 ? [
          "Completou #{answers.length} questões da avaliação",
          "#{satisfactory_count} respostas marcadas como satisfatórias",
          "WSI Score de #{avg_score.round(2)}/#{WSI_SCALE_MAX.to_i} indica nível #{wsi_level} segundo Modelo Dreyfus"
        ] : [ "Análise detalhada não disponível" ],
        weaknesses: satisfactory_count < answers.length ? [
          "WSI Score de #{avg_score.round(2)}/#{WSI_SCALE_MAX.to_i} indica necessidade de validação adicional",
          "#{answers.length - satisfactory_count} respostas requerem revisão segundo critérios WSI"
        ] : [ "Nenhum ponto crítico identificado" ],
        recommendation: recommendation,
        recommendation_justification: justification,
        next_steps: next_steps,
        approval_criteria: {
          wsi_threshold: WSI_AUTO_APPROVAL_MIN,
          meets_threshold: avg_score >= WSI_AUTO_APPROVAL_MIN,
          percentile_rank: avg_score >= WSI_AUTO_APPROVAL_MIN ? "Top 25%" : "Abaixo do esperado",
          auto_approval_eligible: auto_approval
        }
      }
    end

    def build_deterministic_analysis(payload)
      answers = payload[:answers] || []
      skills = answers.map.with_index do |answer, i|
        analysis_data = answer[:analysis_data].is_a?(Hash) ? answer[:analysis_data] : {}
        scoring = fetch_hash(analysis_data, :scoring)
        bloom = fetch_hash(analysis_data, :bloom)
        dreyfus = fetch_hash(analysis_data, :dreyfus)
        big_five = fetch_hash(analysis_data, :big_five)
        cbi_star = fetch_hash(analysis_data, :cbi_star)

        {
          skill_name: answer[:title] || "Questão #{i + 1}",
          competence_type: answer[:competence_type] || "N/A",
          bloom_level_expected: answer[:bloom_level] || "N/A",
          bloom_level_achieved: (bloom[:score] || 0).to_i,
          dreyfus_target: answer[:dreyfus_target] || "N/A",
          dreyfus_level_achieved: (dreyfus[:score] || 0).to_i,
          ocean_trait: answer[:ocean_trait] || "N/A",
          self_declaration: (scoring[:self_declaration_score] || 0).to_f.round(2),
          context_score: (scoring[:context_score] || 0).to_f.round(2),
          final_score: (answer[:final_skill_score] || scoring[:final_skill_score] || 0).to_f.round(2),
          penalty: (scoring[:penalties_total] || 0).to_f.round(2),
          bonus: (scoring[:bonuses_total] || 0).to_f.round(2),
          evidence_type: "Autodeclaração + Contexto",
          star_evidences: [ cbi_star[:situation], cbi_star[:task], cbi_star[:action], cbi_star[:result] ].compact,
          red_flags: [],
          feedback: comments_feedback(answer[:comments_response], scoring)
        }
      end

      answer_scores = skills.map { |item| item[:final_score].to_f }.reject(&:zero?)
      computed_avg_10 = answer_scores.any? ? (answer_scores.sum / answer_scores.size).round(4) : 0.0
      computed_wsi_score = computed_avg_10.round(2)
      wsi_score = persisted_wsi_score.presence || computed_wsi_score
      dreyfus_level = persisted_dreyfus_level.presence || infer_dreyfus_level(skills)
      wsi_classification = classify_wsi(wsi_score)
      wsi_level = persisted_wsi_level.presence || dreyfus_label(dreyfus_level)

      full_analysis_text = default_full_analysis(payload[:candidate_name], payload[:job_title], wsi_score, wsi_classification, dreyfus_level)

      {
        wsi_score: wsi_score,
        wsi_classification: wsi_classification,
        wsi_level: wsi_level,
        dreyfus_level: dreyfus_level,
        skills_analysis: skills,
        behavioral_analysis: build_behavioral_analysis(answers),
        approval_criteria: build_approval_criteria(wsi_score),
        full_analysis: full_analysis_text,
        summary: narrative_excerpt_from_full_analysis(full_analysis_text),
        strengths: default_strengths(skills),
        weaknesses: default_weaknesses(skills),
        recommendation: default_recommendation(wsi_score),
        recommendation_justification: default_recommendation_justification(wsi_score, wsi_classification),
        next_steps: default_next_steps(wsi_score)
      }
    end

    def fetch_hash(data, key)
      value = data[key] || data[key.to_s]
      value.is_a?(Hash) ? value.deep_symbolize_keys : {}
    end

    def comments_feedback(comments, scoring)
      feedback = comments["feedback_for_recruiter"] || comments[:feedback_for_recruiter]
      feedback.presence || "Score calculado deterministicamente: #{(scoring[:final_skill_score] || 0).to_f.round(2)}"
    end

    def persisted_wsi_score
      return nil unless @evaluation_candidate.score.present? && @evaluation_candidate.score.to_f > 0

      @evaluation_candidate.score.to_f.round(2)
    end

    def persisted_wsi_level
      @evaluation_candidate.wsi_level.presence
    end

    def persisted_dreyfus_level
      mapping = {
        "novice" => 1,
        "advanced beginner" => 2,
        "competent" => 3,
        "proficient" => 4,
        "expert" => 5
      }
      return nil if @evaluation_candidate.wsi_level.blank?

      mapping[@evaluation_candidate.wsi_level.to_s.downcase]
    end

    def infer_dreyfus_level(skills)
      values = skills.map { |item| item[:dreyfus_level_achieved].to_i }.reject(&:zero?)
      return 0 if values.blank?

      (values.sum.to_f / values.size).round
    end

    def classify_wsi(score)
      s = score.to_f.clamp(0.0, WSI_SCALE_MAX)
      return "Exceptional" if s >= 9.0
      return "Excellent" if s >= 8.0
      return "High" if s >= 7.0
      return "Medium" if s >= 6.0
      return "Below average" if s >= 4.5

      "Regular"
    end

    def infer_dreyfus_from_wsi(score_0_10)
      s = score_0_10.to_f.clamp(0.0, WSI_SCALE_MAX)
      ((s / 2.0) + 0.5).floor.clamp(1, 5)
    end

    def dreyfus_label(level)
      {
        1 => "Novice",
        2 => "Advanced Beginner",
        3 => "Competent",
        4 => "Proficient",
        5 => "Expert"
      }[level.to_i] || "N/A"
    end

    def build_behavioral_analysis(answers)
      traits = {
        openness: [],
        conscientiousness: [],
        extraversion: [],
        agreeableness: [],
        neuroticism: []
      }

      answers.each do |answer|
        big_five = fetch_hash(answer[:analysis_data] || {}, :big_five)
        traits[:openness] << big_five[:o].to_f if big_five[:o]
        traits[:conscientiousness] << big_five[:c].to_f if big_five[:c]
        traits[:extraversion] << big_five[:e].to_f if big_five[:e]
        traits[:agreeableness] << big_five[:a].to_f if big_five[:a]
        traits[:neuroticism] << big_five[:n].to_f if big_five[:n]
      end

      {
        communication: "Análise consolidada via scoring determinístico com suporte de metadados da avaliação.",
        consistency: "Coerência entre componentes do score determinístico (técnico: 35% autodeclaração, 40% contexto, 25% alinhamento Bloom; comportamental: 35% STAR, 40% traits, 25% Bloom).",
        depth: "Profundidade inferida por Bloom, Dreyfus e completude STAR.",
        ocean_traits: {
          openness: avg_text(traits[:openness]),
          conscientiousness: avg_text(traits[:conscientiousness]),
          extraversion: avg_text(traits[:extraversion]),
          agreeableness: avg_text(traits[:agreeableness]),
          neuroticism: avg_text(traits[:neuroticism])
        }
      }
    end

    def avg_text(values)
      return "N/A" if values.blank?

      values.sum.fdiv(values.size).round(2).to_s
    end

    def build_approval_criteria(score)
      {
        wsi_threshold: WSI_AUTO_APPROVAL_MIN,
        meets_threshold: score >= WSI_AUTO_APPROVAL_MIN,
        percentile_rank: score >= WSI_AUTO_APPROVAL_MIN ? "Top 25%" : "Abaixo do esperado",
        auto_approval_eligible: score >= WSI_AUTO_APPROVAL_MIN
      }
    end

    def default_full_analysis(candidate_name, job_title, score, classification, dreyfus_level)
      "#{candidate_name} obteve WSI #{score}/#{WSI_SCALE_MAX.to_i} (#{classification}) para a vaga #{job_title}. " \
      "A análise determinística indicou nível Dreyfus #{dreyfus_level} com base em Bloom, STAR, Big Five e evidências de contexto."
    end

    def resolve_narrative_summary(parsed, full_analysis_text)
      raw = (parsed["summary"].presence || parsed["analise_resumida"]).to_s.strip
      full = full_analysis_text.to_s.strip

      return narrative_excerpt_from_full_analysis(full) if raw.blank?
      return narrative_excerpt_from_full_analysis(full) if summary_placeholder?(raw)

      raw
    end

    def summary_placeholder?(text)
      text == SUMMARY_JSON_PLACEHOLDER
    end

    def narrative_excerpt_from_full_analysis(full_text)
      return "" if full_text.blank?

      collapsed = full_text.gsub(/\s+/, " ").strip
      sentences = collapsed.split(/(?<=[.!?])\s+/).map(&:strip).reject(&:blank?)

      if sentences.size >= 2
        sentences.first(3).join(" ")
      else
        collapsed.truncate(600, omission: "...")
      end
    end

    def default_strengths(skills)
      top = skills.sort_by { |item| -item[:final_score].to_f }.first(3)
      return [ "Sem evidências suficientes para destacar pontos fortes." ] if top.blank?

      top.map do |item|
        "#{item[:skill_name]} com score #{item[:final_score].round(2)} e Dreyfus #{item[:dreyfus_level_achieved]}."
      end
    end

    def default_weaknesses(skills)
      bottom = skills.sort_by { |item| item[:final_score].to_f }.first(2)
      return [ "Sem lacunas críticas identificadas." ] if bottom.blank?

      bottom.map do |item|
        "#{item[:skill_name]} requer aprofundamento (score #{item[:final_score].round(2)})."
      end
    end

    def default_recommendation(score)
      return "APPROVED" if score >= WSI_AUTO_APPROVAL_MIN
      return "ADDITIONAL_ANALYSIS" if score >= WSI_REVIEW_BAND_MIN

      "NOT_RECOMMENDED"
    end

    def default_recommendation_justification(score, classification)
      "Recomendação baseada no WSI #{score}/#{WSI_SCALE_MAX.to_i} classificado como #{classification}."
    end

    def default_next_steps(score)
      return "Avançar para entrevista técnica focando validação prática dos principais pontos fortes." if score >= WSI_AUTO_APPROVAL_MIN
      return "Executar entrevista complementar para validar lacunas identificadas antes de decisão final." if score >= WSI_REVIEW_BAND_MIN

      "Encerrar processo atual e manter candidato no banco para vagas com aderência maior."
    end
  end
end
