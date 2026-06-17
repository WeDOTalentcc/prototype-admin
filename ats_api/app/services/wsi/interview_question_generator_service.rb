# frozen_string_literal: true

module Wsi
  class InterviewQuestionGeneratorService
    MAX_ATTEMPTS = 3
    DEFAULT_MAX_OUTPUT_TOKENS = begin
      v = ENV.fetch("WSI_F11_INTERVIEW_MAX_OUTPUT_TOKENS", "4096").to_i
      v.positive? ? v : 4096
    end
    F11_REPORT_VERSION = "1"

    def self.call(evaluation_candidate:, top_gaps:, top_strengths: [], triage_question_texts: [], persist: true)
      new(
        evaluation_candidate: evaluation_candidate,
        top_gaps: top_gaps,
        top_strengths: top_strengths,
        triage_question_texts: triage_question_texts,
        persist: persist
      ).call
    end

    def initialize(evaluation_candidate:, top_gaps:, top_strengths: [], triage_question_texts: [], persist: true)
      @evaluation_candidate = evaluation_candidate
      @top_gaps = Array(top_gaps)
      @top_strengths = Array(top_strengths)
      @triage_question_texts = triage_question_texts
      @persist = persist
    end

    def call
      return stubbed_result if Rails.env.test?

      gaps_payload = format_gaps(@top_gaps)
      attempt = 0
      last_error = nil

      while attempt < MAX_ATTEMPTS
        attempt += 1
        begin
          token_budget = [ DEFAULT_MAX_OUTPUT_TOKENS * attempt, 8192 ].min
          response = Llm::Gateway.chat(
            messages: [
              { role: "system", content: system_prompt },
              { role: "user", content: build_user_prompt(gaps_payload) }
            ],
            temperature: 0.6,
            max_tokens: [ token_budget, 600 ].min,
            tracking: { operation: "wsi.f11_interview_questions" }
          )
          content = response.dig("choices", 0, "message", "content")
          if content.blank?
            last_error = "blank_model_response"
            Rails.logger.warn("⚠️ [InterviewQuestionGeneratorService] attempt #{attempt}: blank content from Gemini")
            next
          end

          parsed = parse_json(content)
          if parsed.blank?
            last_error = truncated_completion?(content) ? "json_parse_failed_truncated" : "json_parse_failed"
            Rails.logger.warn("⚠️ [InterviewQuestionGeneratorService] attempt #{attempt}: #{last_error} snippet=#{content.to_s[0..400].inspect}")
            next
          end

          questions = normalize_interview_questions(parsed)
          if questions.size >= 2
            result = {
              success: true,
              interview_questions: questions.first(2),
              generation_metadata: extract_generation_metadata(parsed),
              llm_fallback: false
            }
            persist_f11_interview_section!(result) if @persist
            return result
          end

          last_error = "insufficient_questions(#{questions.size})"
          Rails.logger.warn("⚠️ [InterviewQuestionGeneratorService] attempt #{attempt}: #{last_error}")
        rescue StandardError => e
          last_error = e.message
          Rails.logger.warn("⚠️ [InterviewQuestionGeneratorService] attempt #{attempt}: #{e.class} #{e.message}")
        end
      end

      {
        success: false,
        interview_questions: [],
        generation_metadata: {
          "error" => last_error.presence || "unknown_after_#{MAX_ATTEMPTS}_attempts",
          "hint" => "See logs for ⚠️ [InterviewQuestionGeneratorService]; run reload! if code changed"
        },
        llm_fallback: true
      }
    end

    private

    def stubbed_result
      {
        success: true,
        interview_questions: [
          {
            "question_number" => 1,
            "area" => "technical",
            "gap_focus" => "gap_1",
            "question_text" => "Describe a concrete situation where you applied this skill and measured the outcome."
          },
          {
            "question_number" => 2,
            "area" => "behavioral",
            "gap_focus" => "gap_2",
            "question_text" => "Tell me about a time you aligned stakeholders under pressure; what was your role and the measurable result?"
          }
        ],
        generation_metadata: { "stub" => true },
        llm_fallback: false
      }
    end

    def system_prompt
      <<~PROMPT.strip
        Você é um especialista em entrevistas comportamentais estruturadas (CBI).
        Gere EXATAMENTE 2 perguntas para entrevista presencial com base nos gaps identificados na triagem.

        PROPÓSITO DAS PERGUNTAS:
        - Aprofundar as competências em que a triagem indicou gap ou baixa profundidade
        - Obter evidências que a triagem textual não conseguiu capturar
        - Seguir o formato CBI-STAR: pedir situação real passada + ação + resultado

        REGRAS DE FORMATO:
        - Cada pergunta deve ter entre 1 e 3 frases
        - Pergunta 1: focar no gap de MAIOR severidade (técnico ou comportamental)
        - Pergunta 2: focar no segundo maior gap — de tipo diferente do primeiro
          (se pergunta 1 é técnica → pergunta 2 deve ser comportamental, e vice-versa)
        - Não repetir perguntas já feitas na triagem (lista fornecida no USER)
        - Perguntas abertas — sem opções embutidas

        REGRAS DE FAIRNESS (INEGOCIÁVEIS — BASE LEGAL: LGPD ART. 6º, CLT ART. 5º, CF ART. 5º):
        - Linguagem NEUTRA em gênero: "a pessoa candidata", "você", "quem estava no projeto"
          PROIBIDO: "o candidato", "ele/ela", "o gerente", marcadores de gênero em cenários
        - Cenário EXCLUSIVAMENTE profissional: projeto, equipe, entrega, decisão técnica
          PROIBIDO: situações familiares, saúde, filhos, vida fora do trabalho, religião
        - PROIBIDO referenciar características protegidas: raça, etnia, origem, orientação sexual,
          estado civil, deficiência, faixa etária, nacionalidade
        - PROIBIDO termos de viés implícito: "nativo", "jovem", "recém-formado",
          "universidades de primeira linha", "boa aparência"
        - Calibrar nível de complexidade à senioridade — não ao candidato específico

        REGRAS DE AUDITABILIDADE:
        - Retornar campo "gap_focus" para cada pergunta: qual gap está sendo investigado
        - Retornar campo "expected_evidence": o que uma boa resposta deveria conter
        - Retornar campo "bloom_target" e "dreyfus_target": calibração esperada

        Saída: um único objeto JSON válido, sem markdown, sem texto fora do JSON.
        Inclua "generation_metadata" com gaps_used, gaps_skipped (array de strings), fairness_check (string curta).
        Para "red_flags" em cada pergunta: texto curto descrevendo o que indicaria gap persistente (conforme metodologia F11.5).
      PROMPT
    end

    def build_user_prompt(gaps_payload)
      job = @evaluation_candidate.job
      seniority_key = Wsi::Constants.seniority_key(job)
      cal = Wsi::Constants.seniority_calibration(seniority_key)
      seniority_label = if job&.seniority.present?
        Job::SENIORITY[job.seniority] || job.seniority.to_s
      else
        "não informado"
      end
      bloom_line = cal[:bloom_expected].to_s
      drey_line = "#{cal[:dreyfus_technical_level]} — #{cal[:dreyfus_technical_label]}"
      company_context = [ job&.company&.name, job&.description.to_s[0..400] ].compact.join(" | ")

      strengths_payload = format_strengths(@top_strengths)
      <<~PROMPT.strip
        Senioridade da vaga: #{seniority_label}
        Bloom esperado para esta senioridade: #{bloom_line}
        Dreyfus esperado: #{drey_line}
        Contexto da vaga / empresa: #{company_context.presence || "não informado"}

        Gaps identificados na triagem (ordenados por severidade — ALTO→MÉDIO→BAIXO):
        #{gaps_payload}

        Pontos fortes identificados (para não perguntar sobre o que já está comprovado):
        #{strengths_payload}

        Perguntas JÁ feitas na triagem (não repetir):
        #{Array(@triage_question_texts).join("\n---\n")}

        Retorne o seguinte JSON (sem texto fora do JSON):
        {
          "interview_questions": [
            {
              "question_number": 1,
              "area": "technical | behavioral",
              "competencia_label": "nome da skill ou trait investigada",
              "gap_focus": "descrição em 1 frase do gap que esta pergunta investiga",
              "question_text": "texto completo da pergunta — pronta para ser lida pelo consultor",
              "bloom_target": 1-6,
              "bloom_label": "Lembrar|Compreender|Aplicar|Analisar|Avaliar|Criar",
              "dreyfus_target": 1-5,
              "dreyfus_label": "Novice|Advanced Beginner|Competent|Proficient|Expert",
              "expected_evidence": "o que uma resposta de qualidade deveria incluir (para o consultor)",
              "red_flags": "o que indicaria que o gap confirmado na triagem persiste"
            },
            {
              "question_number": 2,
              "area": "technical | behavioral",
              "competencia_label": "nome da skill ou trait investigada",
              "gap_focus": "descrição em 1 frase do gap que esta pergunta investiga",
              "question_text": "texto completo da pergunta — pronta para ser lida pelo consultor",
              "bloom_target": 1-6,
              "bloom_label": "Lembrar|Compreender|Aplicar|Analisar|Avaliar|Criar",
              "dreyfus_target": 1-5,
              "dreyfus_label": "Novice|Advanced Beginner|Competent|Proficient|Expert",
              "expected_evidence": "o que uma resposta de qualidade deveria incluir (para o consultor)",
              "red_flags": "o que indicaria que o gap confirmado na triagem persiste"
            }
          ],
          "generation_metadata": {
            "gaps_used": ["gap 1 selecionado", "gap 2 selecionado"],
            "gaps_skipped": ["gaps não cobertos — motivo"],
            "fairness_check": "confirmação de que as perguntas não contêm viés ou atributo protegido"
          }
        }
      PROMPT
    end

    def format_strengths(items)
      return "(nenhum ponto forte destacado)" if items.blank?

      items.map.with_index do |g, idx|
        if g.is_a?(Wsi::GapAnalyzer::GapItem)
          "[#{idx + 1}] #{g.label} (#{g.tipo}) score #{g.score_obtained}/10"
        else
          g.to_s
        end
      end.join("\n")
    end

    def format_gaps(gaps)
      gaps.map.with_index do |g, idx|
        sev = g.is_a?(Wsi::GapAnalyzer::GapItem) ? g.severidade.to_s.upcase : g.to_s
        label = g.is_a?(Wsi::GapAnalyzer::GapItem) ? g.label : "n/a"
        score = g.is_a?(Wsi::GapAnalyzer::GapItem) ? g.score_obtained : "n/a"
        tipo = g.is_a?(Wsi::GapAnalyzer::GapItem) ? g.tipo : "n/a"
        "[#{idx + 1}] [#{sev}] #{label} (#{tipo}) score #{score}/10"
      end.join("\n")
    end

    def parse_json(text)
      return nil if text.blank?

      cleaned = strip_markdown_fences(text)
      parsed = try_json_parse(cleaned)
      return parsed if parsed.present?

      extracted = extract_json_object(cleaned)
      try_json_parse(extracted) if extracted.present?
    end

    def strip_markdown_fences(text)
      t = text.to_s.strip
      t = t.sub(/\A```(?:json)?\s*/i, "")
      t = t.sub(/\s*```\s*\z/m, "")
      t.strip
    end

    def truncated_completion?(text)
      s = text.to_s
      return true if s.present? && !s.rstrip.end_with?("}", "]")

      open = s.count("{")
      s.count("}") < open
    end

    def try_json_parse(string)
      return nil if string.blank?

      JSON.parse(string)
    rescue JSON::ParserError
      nil
    end

    def extract_json_object(text)
      start_idx = text.index("{")
      end_idx = text.rindex("}")
      return nil unless start_idx && end_idx && end_idx > start_idx

      text[start_idx..end_idx]
    end

    def normalize_interview_questions(parsed)
      if parsed.is_a?(Array)
        return parsed.filter_map do |item|
          next item if item.is_a?(Hash)

          { "question_text" => item.to_s } if item.present?
        end
      end

      return [] unless parsed.is_a?(Hash)

      h = parsed.deep_stringify_keys
      raw = h["interview_questions"] || h["questions"] || h["suggested_questions"] || h["cbi_questions"]
      list = Array(raw).compact
      list.filter_map do |item|
        next item if item.is_a?(Hash)

        { "question_text" => item.to_s } if item.present?
      end
    end

    def extract_generation_metadata(parsed)
      return {} unless parsed.is_a?(Hash)

      parsed["generation_metadata"] || parsed[:generation_metadata] || {}
    end

    def persist_f11_interview_section!(payload)
      ec = @evaluation_candidate
      return unless ec.respond_to?(:f11_report_json)

      base = ec.f11_report_json.is_a?(Hash) ? ec.f11_report_json.deep_stringify_keys : {}
      sections = (base["sections"] || {}).deep_stringify_keys
      existing_7 = (sections["7"] || {}).deep_stringify_keys

      merged_7 = existing_7.merge(
        "interview_questions" => stringify_interview_items(payload[:interview_questions]),
        "interview_generation" => {
          "llm_fallback" => payload[:llm_fallback],
          "metadata" => (payload[:generation_metadata] || {}).deep_stringify_keys
        }
      )
      sections["7"] = merged_7
      base["sections"] = sections
      base["report_id"] ||= ec.uid
      base["methodology_version"] ||= "2.0"
      base["report_version"] ||= F11_REPORT_VERSION

      now = Time.current
      ec.update_columns(
        f11_report_json: base,
        report_generated_at: now,
        report_version: base["report_version"],
        f11_report_stale: false,
        updated_at: now
      )
    rescue StandardError => e
      Rails.logger.error("❌ [InterviewQuestionGeneratorService] f11_report_json persist failed: #{e.class} #{e.message}")
      raise
    end

    def stringify_interview_items(list)
      Array(list).map do |item|
        h = item.is_a?(Hash) ? item : { "question_text" => item.to_s }
        h.deep_stringify_keys
      end
    end
  end
end
