module Candidates
  module Search
    class JobDescriptionProcessor
      ProcessedJD = Struct.new(
        :required_skills,
        :nice_to_have_skills,
        :seniority_range,
        :role_titles,
        :industry_keywords,
        :experience_range,
        :search_queries,
        :boost_config,
        keyword_init: true
      )

      JD_INDICATORS = [
        /\b(requisitos|requirements|qualifica[çc][õo]es)\b/i,
        /\b(responsabilidades|responsibilities|atribui[çc][õo]es)\b/i,
        /\b(desej[aá]vel|nice.?to.?have|diferencial)\b/i,
        /\b(vaga|position|oportunidade|job)\b/i,
        /\b(oferecemos|we.?offer|benef[íi]cios)\b/i,
        /\b(contrata[çc][ãa]o|hiring|recrutamento)\b/i
      ].freeze

      RESUME_INDICATORS = [
        /\b(experi[êe]ncia\s+profissional|professional\s+experience)\b/i,
        /\b(forma[çc][ãa]o|education|gradua[çc][ãa]o)\b/i,
        /\b(objetivo|resumo|summary|sobre\s+mim)\b/i,
        /\b(habilidades|skills|compet[êe]ncias)\b/i,
        /@\w+\.(com|br|org)/,
        /linkedin\.com/i,
        /github\.com/i
      ].freeze

      def initialize; end

      def process(jd_text)
        return build_empty_result if jd_text.blank?

        document_type = detect_document_type(jd_text)
        return build_empty_result unless document_type == :job_description

        processed = extract_jd_structure(jd_text)

        ProcessedJD.new(
          required_skills: processed[:required_skills],
          nice_to_have_skills: processed[:nice_to_have_skills],
          seniority_range: processed[:seniority_range],
          role_titles: processed[:role_titles],
          industry_keywords: processed[:industry_keywords],
          experience_range: processed[:experience_range],
          search_queries: generate_search_queries(processed),
          boost_config: generate_boost_config(processed)
        )
      end

      def detect_document_type(text)
        jd_score = JD_INDICATORS.count { |pattern| text.match?(pattern) }
        resume_score = RESUME_INDICATORS.count { |pattern| text.match?(pattern) }

        return :job_description if jd_score > resume_score && jd_score >= 2
        return :resume if resume_score > jd_score && resume_score >= 2

        has_requirements = text.match?(/requisitos|requirements/i)
        has_responsibilities = text.match?(/responsabilidades|responsibilities/i)

        return :job_description if has_requirements && has_responsibilities

        :unknown
      end

      private

      def extract_jd_structure(jd_text)
        truncated = jd_text.to_s[0, 5000]
        prompt = build_extraction_prompt(truncated)

        response = Llm::Gateway.chat(
          messages: [ { role: "user", content: prompt } ],
          temperature: 0.2,
          max_tokens: 700,
          tracking: { operation: "search.job_description_extraction" }
        )

        content = response.dig("choices", 0, "message", "content").to_s
        parsed = parse_jd_json(content)

        return parsed if parsed.present?

        Rails.logger.warn("[JobDescriptionProcessor] LLM extraction failed, using fallback")
        extract_jd_fallback(jd_text)
      rescue => e
        Rails.logger.error("[JobDescriptionProcessor] Extraction failed: #{e.message}")
        extract_jd_fallback(jd_text)
      end

      def build_extraction_prompt(text)
        <<~PROMPT
          Analise esta descrição de vaga e extraia os requisitos estruturados.
          Descrição da vaga (truncado):
          #{text}

          Retorne APENAS um objeto JSON válido, sem markdown. Exemplo:
          {
            "required_skills": ["Ruby on Rails", "PostgreSQL", "Redis"],
            "nice_to_have_skills": ["React", "AWS", "Docker"],
            "seniority_range": {"min": "pleno", "max": "senior"},
            "role_titles": ["Engenheiro de Software Backend", "Desenvolvedor Ruby"],
            "industry_keywords": ["fintech", "SaaS"],
            "experience_range": {"min": 3, "max": 8}
          }

          Separe claramente skills obrigatórias (required) de desejáveis (nice-to-have).
          Use termos genéricos e em português.
        PROMPT
      end

      def parse_jd_json(content)
        return nil if content.blank?

        raw = content.gsub(/\A\s*```(?:json)?\s*/i, "").gsub(/\s*```\s*\z/, "").strip
        start_idx = raw.index("{")
        return nil unless start_idx

        depth = 0
        end_idx = nil
        raw[start_idx..].each_char.with_index do |c, i|
          depth += 1 if c == "{"
          depth -= 1 if c == "}"
          if depth == 0
            end_idx = start_idx + i
            break
          end
        end

        json_str = end_idx ? raw[start_idx..end_idx] : raw[start_idx..]
        json_str += "]" while json_str.count("[") > json_str.count("]")
        json_str += "}" while json_str.count("{") > json_str.count("}")

        data = JSON.parse(json_str)
        return nil unless data.is_a?(Hash)

        {
          required_skills: Array(data["required_skills"]).map(&:to_s).reject(&:blank?),
          nice_to_have_skills: Array(data["nice_to_have_skills"]).map(&:to_s).reject(&:blank?),
          seniority_range: parse_seniority_range(data["seniority_range"]),
          role_titles: Array(data["role_titles"]).map(&:to_s).reject(&:blank?),
          industry_keywords: Array(data["industry_keywords"]).map(&:to_s).reject(&:blank?),
          experience_range: parse_experience_range(data["experience_range"])
        }
      rescue JSON::ParserError
        nil
      end

      def parse_seniority_range(range)
        return { min: :pleno, max: :senior } unless range.is_a?(Hash)

        {
          min: range["min"]&.to_sym || :pleno,
          max: range["max"]&.to_sym || :senior
        }
      end

      def parse_experience_range(range)
        return { min: 3, max: 8 } unless range.is_a?(Hash)

        {
          min: range["min"]&.to_i || 3,
          max: range["max"]&.to_i || 8
        }
      end

      def extract_jd_fallback(text)
        lower = text.downcase

        required = extract_skills_from_section(text, /requisitos?\s+(obrigat[óo]rios?|mandatórios?|essenciais?)/i)
        required = extract_common_skills(text) if required.empty?

        nice_to_have = extract_skills_from_section(text, /desej[aá]vel|nice.?to.?have|diferencial/i)

        {
          required_skills: required.first(8),
          nice_to_have_skills: nice_to_have.first(6),
          seniority_range: extract_seniority_range(lower),
          role_titles: extract_role_titles(text),
          industry_keywords: extract_industry_keywords(lower),
          experience_range: extract_experience_range(text)
        }
      end

      def extract_skills_from_section(text, section_pattern)
        match = text.match(section_pattern)
        return [] unless match

        section_start = match.begin(0)
        section_text = text[section_start, 1000]

        extract_common_skills(section_text)
      end

      def extract_common_skills(text)
        tech_terms = %w[
          ruby rails php laravel javascript node react vue python java
          postgres mysql redis elasticsearch mongodb docker kubernetes aws
          typescript kotlin swift go golang scala c# dotnet angular
          git agile scrum rest api graphql microservices
        ]

        lower = text.downcase
        tech_terms.select { |t| lower.include?(t) }.map(&:titleize).uniq
      end

      def extract_seniority_range(text)
        levels = []
        levels << :junior if text.match?(/\bjunior\b/i)
        levels << :pleno if text.match?(/\bpleno\b/i)
        levels << :senior if text.match?(/\bsenior\b/i)

        return { min: :pleno, max: :senior } if levels.empty?

        order = { junior: 1, pleno: 2, senior: 3, lead: 4, principal: 5 }
        sorted = levels.sort_by { |l| order[l] || 2 }

        { min: sorted.first, max: sorted.last }
      end

      def extract_role_titles(text)
        titles = []

        titles << "Engenheiro de Software" if text.match?(/engenheiro\s+(de\s+)?software/i)
        titles << "Desenvolvedor" if text.match?(/desenvolvedor|developer/i)
        titles << "Desenvolvedor Backend" if text.match?(/backend/i)
        titles << "Desenvolvedor Full-stack" if text.match?(/full.?stack/i)

        titles.presence || [ "Desenvolvedor" ]
      end

      def extract_industry_keywords(text)
        keywords = []
        keywords << "fintech" if text.match?(/fintech|financeiro|banco/i)
        keywords << "SaaS" if text.match?(/saas|software.?as.?a.?service/i)
        keywords << "e-commerce" if text.match?(/e-commerce|ecommerce|varejo/i)
        keywords << "healthtech" if text.match?(/sa[úu]de|health/i)

        keywords.presence || [ "tecnologia" ]
      end

      def extract_experience_range(text)
        years_match = text.match(/(\d+)\s*(?:a|até|-)\s*(\d+)\s*anos/i)
        return { min: years_match[1].to_i, max: years_match[2].to_i } if years_match

        min_match = text.match(/(?:m[íi]nimo|at least)\s*(\d+)\s*anos/i)
        return { min: min_match[1].to_i, max: 99 } if min_match

        { min: 3, max: 8 }
      end

      def generate_search_queries(processed)
        queries = []

        if processed[:role_titles].any? && processed[:required_skills].any?
          queries << "#{processed[:role_titles].first} #{processed[:required_skills].first(3).join(' ')}"
        end

        if processed[:required_skills].any?
          queries << processed[:required_skills].first(5).join(" ")
        end

        if processed[:role_titles].any? && processed[:seniority_range][:min].present?
          queries << "#{processed[:seniority_range][:min]} #{processed[:role_titles].first}"
        end

        queries.compact.uniq
      end

      def generate_boost_config(processed)
        required_skill_ids = convert_skill_names_to_ids(processed[:required_skills])
        nice_to_have_skill_ids = convert_skill_names_to_ids(processed[:nice_to_have_skills])

        config = {}

        if required_skill_ids.any?
          config[:required_skill_match] = {
            weight: 0.15,
            skill_ids: required_skill_ids
          }
        end

        if nice_to_have_skill_ids.any?
          config[:nice_to_have_match] = {
            weight: 0.05,
            skill_ids: nice_to_have_skill_ids
          }
        end

        if processed[:seniority_range].present?
          config[:seniority_match] = {
            weight: 0.10,
            range: processed[:seniority_range]
          }
        end

        if processed[:experience_range].present?
          config[:experience_match] = {
            weight: 0.08,
            range: processed[:experience_range]
          }
        end

        config
      end

      def convert_skill_names_to_ids(skill_names)
        return [] if skill_names.blank?

        Skill.where("LOWER(name) IN (?)", skill_names.map(&:downcase))
             .pluck(:id)
      end

      def build_empty_result
        ProcessedJD.new(
          required_skills: [],
          nice_to_have_skills: [],
          seniority_range: { min: :pleno, max: :senior },
          role_titles: [],
          industry_keywords: [],
          experience_range: { min: 0, max: 99 },
          search_queries: [],
          boost_config: {}
        )
      end
    end
  end
end
