# frozen_string_literal: true

module Wsi
  # Invoca o LLM para enriquecer o Job Description seguindo o prompt canônico §1.5
  # da metodologia WSI. Não persiste em `jobs` — o cliente grava `lia_job_description`
  # e `jd_quality_score` quando confirmar (ex.: atualização da vaga pelo front).
  #
  # Pré-condição: score de qualidade >= 30 em `job.jd_quality_score` ou em `jd_quality_score:` passado explicitamente.
  class JdEnrichmentService
    TEMPERATURE         = 0.3
    MAX_TOKENS          = 9000
    MIN_QUALITY_SCORE   = 30
    MIN_USEFUL_WORDS    = 50

    WORK_MODEL_MAP = {
      true  => "remoto",
      false => "presencial"
    }.freeze

    def initialize(job:, jd_quality_score: nil)
      @job               = job
      @jd_quality_score  = jd_quality_score
    end

    def self.call(job:, model: nil, jd_quality_score: nil)
      new(job: job, model: model, jd_quality_score: jd_quality_score).call
    end

    def call
      return failure("jd_quality_score_missing") if quality_score.blank?
      return failure("jd_quality_below_threshold") if quality_score["score"].to_i < MIN_QUALITY_SCORE
      return failure("jd_too_short") if useful_word_count < MIN_USEFUL_WORDS

      response = call_llm
      parsed   = parse_response(response)

      return failure("invalid_llm_response") if parsed.blank?

      payload = build_payload(parsed)

      { success: true, lia_job_description: payload }
    rescue StandardError => e
      failure("enrichment_failed: #{e.message}")
    end

    private

    attr_reader :job

    def quality_score
      @resolved_quality_score ||= @jd_quality_score.presence || @job.jd_quality_score.presence || {}
    end

    def useful_word_count
      [ @job.description, @job.responsibilities, @job.title ]
        .map { |f| f.to_s.split.length }
        .sum
    end

    def call_llm
      Llm::Gateway.chat(
        messages: [
          { role: "system", content: system_prompt },
          { role: "user",   content: masked_user_prompt }
        ],
        temperature: TEMPERATURE,
        max_tokens:  MAX_TOKENS,
        tracking:    { operation: "wsi.jd_enrichment", job_id: @job.id }
      )
    end

    def masked_user_prompt
      Wsi::PiiMasker.call(text: user_prompt)
    end

    def parse_response(response)
      content = response.dig("choices", 0, "message", "content").to_s.strip
      json_str = content.gsub(/\A```(?:json)?\s*/, "").gsub(/```\z/, "").strip
      JSON.parse(json_str)
    rescue JSON::ParserError => e
      nil
    end

    def build_payload(parsed)
      enriched_jd = parsed["enriched_jd"] || {}

      {
        "status"         => "pending_review",
        "enriched_at"    => Time.current.iso8601,
        "method_version" => "wsi_f1c_v1",
        "description"    => enriched_jd.delete("description"),
        "quality_report" => parsed["quality_report"],
        "enriched_jd"    => enriched_jd
      }
    end

    def system_prompt
      <<~PROMPT.strip
        Você é um especialista sênior em recrutamento estratégico e análise de competências organizacionais.

        Sua tarefa é analisar o Job Description fornecido pelo recrutador e:
        1. Gerar um relatório de qualidade detalhado
        2. Gerar uma versão enriquecida do JD que preserve a voz e intenção originais

        REGRAS ABSOLUTAS:
        - Nunca inventar requisitos não presentes no JD original
        - Nunca remover informações corretas — apenas clarificar
        - Nunca alterar a senioridade declarada pelo recrutador
        - Manter o tom e cultura da empresa quando identificável
        - Não mencionar os frameworks internos (Big Five, Bloom, Dreyfus, WSI, STAR)
        - Se o JD tiver menos de 50 palavras úteis, retorne imediatamente com "ready_for_processing": false e "level": "critical"
        - Se campos opcionais não forem fornecidos, sinalize em "warnings"; NUNCA invente valores ausentes
        - Quando "Informações complementares" incluírem competências comportamentais, remunerações ou benefícios
          cadastrados na vaga, incorpore-os de forma fiel no JSON e no campo "description"; não invente valores além do informado

        REGRAS DE FAIRNESS E NÃO-DISCRIMINAÇÃO (LGPD ART. 6º, CLT ART. 5º, CF ART. 5º):
        - Use SEMPRE linguagem neutra em gênero: "a pessoa candidata", "você", "quem ocupa este papel"
        - NUNCA use: "ele", "ela", "o candidato ideal", marcadores de gênero, raça, origem, religião
        - NUNCA use termos de viés implícito: "boa aparência", "jovem e dinâmico", "native speaker",
          "recém-formado", "escola particular", "bairros nobres", "universidades de primeira linha"
        - ANTI-BAJULAÇÃO: se o JD for de baixa qualidade, o "executive_summary" deve ser honesto

        OS 10 PRINCÍPIOS DE QUALIDADE:
        P1. Título específico com indicador de senioridade
        P2. Coerência entre senioridade e complexidade das responsabilidades
        P3. Skills técnicas específicas — mínimo 9; decompor skills genéricas em sub-skills
        P4. Responsabilidades com verbos de ação + escopo mensurável
        P5. Competências comportamentais contextualizadas com mapeamento Big Five — mínimo 5
        P6. Ausência de inconsistências internas
        P7. Linguagem inclusiva — sem marcadores de gênero, origem, idade
        P8. Expectativas realistas de mercado
        P9. Contexto suficiente: empresa, setor, tamanho do time, modelo de trabalho
        P10. Densidade ≥ 150 palavras úteis

        REGRAS PARA O CAMPO "description":
        - É o Job Description completo e final, pronto para publicação
        - Deve ser redigido em markdown fluído, seguindo TODAS as regras de fairness acima
        - Estrutura obrigatória: título, sobre a empresa/contexto (se disponível), sobre o papel,
          responsabilidades, skills obrigatórias com contexto, skills desejáveis,
          competências comportamentais, contexto de trabalho (autonomia, modelo, pressão)
        - Linguagem SEMPRE neutra em gênero: "a pessoa candidata", "você", "quem ocupa este papel"
        - Nenhum marcador de gênero, raça, origem, idade ou qualquer atributo protegido
        - Verbos de ação + escopo mensurável nas responsabilidades
        - Mínimo 300 palavras úteis
        - Não mencionar frameworks internos (WSI, Big Five, Bloom, Dreyfus, STAR)

        Retorne APENAS um JSON válido, sem texto fora do JSON.
      PROMPT
    end

    def user_prompt
      seniority_label = @job.seniority.present? ? Job::SENIORITY[@job.seniority] : "não informado"
      work_model      = WORK_MODEL_MAP.fetch(@job.try(:is_remote), "não informado")

      skills_list = if @job.respond_to?(:skill_relationships) && @job.skill_relationships.any?
                      @job.skill_relationships.map { |sr| sr.try(:skill)&.name }.compact
      else
                      []
      end

      behavioral_block = complementary_behavioral_skills_text
      remuneration_block = complementary_remunerations_text
      benefits_block     = complementary_benefits_text

      <<~PROMPT.strip
        Job Description original fornecido pelo recrutador:
        ---
        #{[ @job.description, @job.responsibilities ].compact.join("\n\n")}
        ---

        Informações complementares:
        - Título da vaga: #{@job.title.presence || "não informado"}
        - Senioridade declarada: #{seniority_label}
        - Departamento: não informado
        - Setor / indústria: #{@job.sector.presence || "não informado"}
        - Tamanho da empresa: não informado
        - Modelo de trabalho: #{work_model}
        - Lista de skills técnicas (wizard): #{skills_list.any? ? skills_list.join(", ") : "não informado"}
        - Competências comportamentais (behavioral_skill_relationships):
        #{indent_complementary_lines(behavioral_block)}
        - Remunerações (remuneration_relationships):
        #{indent_complementary_lines(remuneration_block)}
        - Benefícios (benefit_relationships):
        #{indent_complementary_lines(benefits_block)}

        Retorne o seguinte JSON (sem texto fora do JSON):
        {
          "quality_report": {
            "total_score": 0,
            "level": "critical | insufficient | adequate | good | excellent",
            "executive_summary": "string",
            "dimensions": [
              {
                "dimension": "string",
                "score": 0,
                "max_score": 15,
                "status": "ok | warning | critical",
                "finding": "string",
                "suggestion": "string"
              }
            ],
            "critical_issues": [],
            "warnings": [],
            "compliance_flags": {
              "fairness_issues_found": false,
              "fairness_issues": [],
              "fields_missing": []
            },
            "ready_for_processing": true
          },
          "enriched_jd": {
            "standardized_title": "string",
            "confirmed_seniority": "string",
            "about_role": "string",
            "responsibilities": [],
            "required_skills": [
              { "skill": "string", "context": "string" }
            ],
            "preferred_skills": [],
            "behavioral_competencies": [
              { "competency": "string", "context": "string", "big_five_trait": "openness | conscientiousness | extraversion | agreeableness | stability" }
            ],
            "context_signals": {
              "autonomy_level": "low | medium | high",
              "innovation_level": "low | medium | high",
              "pressure_level": "low | medium | high",
              "collaboration_level": "low | medium | high"
            },
            "changes_made": [],
            "fairness_corrections": [],
            "description": "Complete and final job description in markdown, ready for publishing. Minimum 300 useful words. Gender-neutral language. No mention of internal frameworks."
          }
        }
      PROMPT
    end

    def complementary_behavioral_skills_text
      return "não informado" unless job.respond_to?(:behavioral_skill_relationships)

      rels = job.behavioral_skill_relationships.where(is_deleted: false).includes(:behavioral_skill)
      return "não informado" if rels.none?

      rels.filter_map do |bsr|
        name = bsr.behavioral_skill&.name
        next if name.blank?

        level_name = SkillRelationship::SKILL_LEVELS.find { |x| x[:id] == bsr.level_skill }&.dig(:name)
        exp_name   = SkillRelationship::EXPERIENCE_TIMES.find { |x| x[:id] == bsr.experience_time }&.dig(:name)
        parts      = [
          name,
          bsr.priority.present? ? "prioridade #{bsr.priority}" : nil,
          level_name,
          exp_name,
          bsr.description.presence
        ].compact
        "• #{parts.join(" | ")}"
      end.join("\n")
    end

    def complementary_remunerations_text
      return "não informado" unless job.respond_to?(:remuneration_relationships)

      rels = job.remuneration_relationships.where(is_deleted: false).includes(:remuneration)
      return "não informado" if rels.none?

      rels.filter_map do |rr|
        name = rr.remuneration&.name
        next if name.blank?

        period_key = RemunerationRelationship::PERIOD_VALUES.key(rr.period)
        period_txt = period_key.present? ? "período #{period_key}" : (rr.period.present? ? "período_id=#{rr.period}" : nil)
        contracts  = Array.wrap(rr.contract_type).compact_blank
        contract_s = contracts.any? ? "contrato #{contracts.join(", ")}" : nil
        value_s    = rr.value.present? ? "valor #{rr.value}" : nil
        amount_s   = rr.amount.present? ? "valor_fixo #{rr.amount}" : nil
        parts      = [ name, value_s, amount_s, rr.currency, period_txt, contract_s, rr.comments.presence ].compact
        "• #{parts.join(" | ")}"
      end.join("\n")
    end

    def complementary_benefits_text
      return "não informado" unless job.respond_to?(:benefit_relationships)

      rels = job.benefit_relationships.where(is_deleted: false)
      return "não informado" if rels.none?

      rels.filter_map do |br|
        label = br.benefit&.name.presence || br.name
        next if label.blank?

        types = Array.wrap(br.types).compact_blank
        type_s = types.any? ? "tipos #{types.join(", ")}" : nil
        parts  = [ label, type_s, br.type_description.presence, br.description.presence ]
        parts << br.details.truncate(400) if br.details.present?
        parts << "por_dia" if br.is_per_day
        "• #{parts.compact.join(" | ")}"
      end.join("\n")
    end

    def indent_complementary_lines(block)
      return "  #{block}" unless block.include?("\n")

      block.each_line.map { |line| "  #{line.rstrip}" }.join("\n")
    end

    def failure(error)
      Rails.logger.warn "⚠️  [Wsi::JdEnrichmentService] #{error} para Job ##{@job.id}"
      { success: false, error: error }
    end
  end
end
