module Candidates
  module Search
    class ProfileExtractor
      ExtractionResult = Struct.new(
        :profile,
        :confidence,
        :extraction_method,
        :missing_fields,
        keyword_init: true
      )

      REQUIRED_FIELDS = %i[primary_role core_technologies].freeze
      OPTIONAL_FIELDS = %i[seniority years_experience transferable_skills industry].freeze

      def initialize; end

      def extract(text, source_type: :resume)
        return build_empty_result if text.blank?

        profile, method = extract_with_llm(text, source_type)

        profile = normalize_profile(profile)
        missing = find_missing_fields(profile)
        confidence = calculate_confidence(profile, method)

        ExtractionResult.new(
          profile: profile,
          confidence: confidence,
          extraction_method: method,
          missing_fields: missing
        )
      end

      private

      def extract_with_llm(text, source_type)
        truncated = text.to_s[0, 5000]
        prompt = build_prompt(truncated, source_type)

        response = Llm::Gateway.chat(
          messages: [ { role: "user", content: prompt } ],
          temperature: 0.2,
          max_tokens: 500,
          tracking: { operation: "search.profile_extraction" }
        )

        content = response.dig("choices", 0, "message", "content").to_s
        profile = parse_profile_json(content)

        return [ profile, :llm ] if profile.present? && profile["primary_role"].present?

        Rails.logger.warn("[ProfileExtractor] LLM extraction incomplete, trying structured fallback")
        [ extract_structured(text), :structured ]
      rescue => e
        Rails.logger.error("[ProfileExtractor] LLM failed: #{e.message}, using keyword fallback")
        [ extract_keyword_fallback(text), :keyword_fallback ]
      end

      def build_prompt(text, source_type)
        case source_type
        when :job_description
          <<~PROMPT
            Analise esta descrição de vaga e extraia os requisitos para o perfil ideal do candidato.
            Descrição da vaga (truncado):
            #{text}
            Retorne APENAS um objeto JSON válido, sem markdown. Exemplo:
            {"seniority":"senior","years_experience":8,"primary_role":"Engenheiro de Software Backend","core_technologies":["Ruby on Rails","PostgreSQL","Redis"],"transferable_skills":["arquitetura de sistemas","liderança técnica"],"industry":"fintech"}
            Campos obrigatórios: primary_role, core_technologies (array). Use termos genéricos.
          PROMPT
        else
          <<~PROMPT
            Analise este currículo e extraia características-chave para buscar candidatos SIMILARES.
            Currículo (truncado):
            #{text}
            Retorne APENAS um objeto JSON válido, sem markdown. Exemplo:
            {"seniority":"senior","years_experience":10,"primary_role":"CTO engenheiro de software","core_technologies":["Ruby on Rails","PHP","Laravel","Elasticsearch"],"transferable_skills":["liderança técnica","SaaS"],"industry":"tecnologia"}
            Campos obrigatórios: primary_role, core_technologies (array). Use termos genéricos.
          PROMPT
        end
      end

      def parse_profile_json(content)
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
          "seniority" => data["seniority"].to_s.presence,
          "years_experience" => data["years_experience"].is_a?(Numeric) ? data["years_experience"] : nil,
          "primary_role" => data["primary_role"].to_s.presence,
          "core_technologies" => Array(data["core_technologies"]).map(&:to_s).reject(&:blank?).first(5),
          "transferable_skills" => Array(data["transferable_skills"]).map(&:to_s).reject(&:blank?).first(4),
          "industry" => data["industry"].to_s.presence
        }.compact
      rescue JSON::ParserError
        nil
      end

      def extract_structured(text)
        raw = text.to_s[0, 6000].downcase

        seniority = detect_seniority(raw)
        primary_role = detect_primary_role(raw)
        core_tech = extract_technologies(text)
        transferable = extract_transferable_skills(raw)

        {
          "seniority" => seniority,
          "years_experience" => 5,
          "primary_role" => primary_role,
          "core_technologies" => core_tech,
          "transferable_skills" => transferable,
          "industry" => "tecnologia"
        }
      end

      def extract_keyword_fallback(text)
        extract_structured(text)
      end

      def detect_seniority(text)
        return "senior" if text.match?(/\b(cto|ceo|tech\s*lead|gerente|diretor|principal|staff)\b/i)
        return "senior" if text.match?(/\bsenior\b/i)
        return "pleno" if text.match?(/\bpleno\b/i)
        return "junior" if text.match?(/\bjunior\b/i)

        "pleno"
      end

      def detect_primary_role(text)
        return "CTO engenheiro de software" if text.match?(/\bcto\b|chief\s*technology/i)
        return "CEO engenheiro de software" if text.match?(/\bceo\b|chief\s*executive/i)
        return "engenheiro de software" if text.match?(/\b(engenheiro|engineer)\s+(de\s+)?software/i)
        return "desenvolvedor" if text.match?(/\bdesenvolvedor|developer\b/i)

        "desenvolvedor"
      end

      def extract_technologies(text)
        tech_terms = %w[
          ruby rails php laravel javascript node react vue python java elasticsearch
          postgres mysql redis sidekiq docker aws saas nginx heroku unicorn
          typescript kotlin swift go golang scala c# dotnet angular next
        ]

        lower = text.downcase
        found = tech_terms.select { |t| lower.include?(t) }.first(5).map(&:titleize)

        return found if found.any?

        extract_significant_terms(text)
      end

      def extract_significant_terms(text)
        known_caps = %w[Ruby Rails PHP Laravel JavaScript Node React Vue Python Java TypeScript
                       Kotlin Swift Go Scala Angular Next.js AWS Docker Kubernetes]
        found = known_caps.select { |w| text.include?(w) }
        return found.first(5) if found.any?

        words = text[0, 1500].scan(/\b[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9.]{3,}\b/)
        freq = words.each_with_object(Hash.new(0)) { |w, h| h[w] += 1 }
        freq.sort_by { |_, c| -c }.map(&:first).reject { |w| w.length > 25 }.first(5)
      end

      def extract_transferable_skills(text)
        skills = []
        skills << "liderança técnica" if text.match?(/\b(cto|tech\s*lead|equipe|times|gerente)\b/i)
        skills << "SaaS" if text.include?("saas")
        skills << "desenvolvimento web" if text.match?(/\b(web|backend|frontend)\b/i)

        skills.presence || [ "desenvolvimento de software" ]
      end

      def normalize_profile(profile)
        return {} if profile.blank?

        profile.transform_keys(&:to_s).compact
      end

      def find_missing_fields(profile)
        all_fields = REQUIRED_FIELDS + OPTIONAL_FIELDS
        all_fields.reject { |field| profile[field.to_s].present? }
      end

      def calculate_confidence(profile, extraction_method)
        base_confidence = confidence_by_method(extraction_method)
        field_coverage = calculate_field_coverage(profile)
        field_quality = calculate_field_quality(profile)

        (base_confidence * 0.4 + field_coverage * 0.3 + field_quality * 0.3).round(2)
      end

      def confidence_by_method(method)
        {
          llm: 0.85,
          structured: 0.70,
          keyword_fallback: 0.40
        }.fetch(method, 0.30)
      end

      def calculate_field_coverage(profile)
        required_present = REQUIRED_FIELDS.count { |f| profile[f.to_s].present? }
        optional_present = OPTIONAL_FIELDS.count { |f| profile[f.to_s].present? }

        required_score = required_present.to_f / REQUIRED_FIELDS.size
        optional_score = optional_present.to_f / OPTIONAL_FIELDS.size

        (required_score * 0.7 + optional_score * 0.3)
      end

      def calculate_field_quality(profile)
        scores = []

        tech_count = Array(profile["core_technologies"]).size
        scores << (tech_count >= 2 ? 1.0 : tech_count * 0.5)

        role_words = profile["primary_role"].to_s.split.size
        scores << (role_words >= 2 ? 1.0 : 0.5)

        valid_seniorities = %w[junior pleno senior lead principal staff]
        scores << (valid_seniorities.include?(profile["seniority"].to_s.downcase) ? 1.0 : 0.3)

        scores.sum / scores.size
      end

      def build_empty_result
        ExtractionResult.new(
          profile: {},
          confidence: 0.0,
          extraction_method: :empty,
          missing_fields: REQUIRED_FIELDS + OPTIONAL_FIELDS
        )
      end
    end
  end
end
