# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class ProfileSynthesizer
      TIMEOUT_SECONDS = 5.0

      def initialize; end

      def call(base_candidates)
        return default_synthesis if base_candidates.blank?

        profiles_context = build_profiles_context(base_candidates)

        response = call_llm_with_timeout(profiles_context)
        return default_synthesis unless response

        parse_and_validate(response, base_candidates)
      rescue => e
        Rails.logger.error("[ProfileSynthesizer] Error: #{e.message}")
        Rails.logger.error(e.backtrace.first(5).join("\n"))
        default_synthesis
      end

      private

      def build_profiles_context(candidates)
        candidates.map.with_index(1) do |candidate, idx|
          experiences = candidate.experiences&.first(3) || []
          educations = candidate.educations&.first(2) || []

          exp_summary = experiences.map do |exp|
            "- #{exp['title']} at #{exp['company']} (#{exp['start_date']} - #{exp['end_date'] || 'Present'})"
          end.join("\n")

          edu_summary = educations.map do |edu|
            "- #{edu['degree']} in #{edu['field_of_study']} at #{edu['school']}"
          end.join("\n")

          <<~PROFILE
            ## Profile #{idx}
            Name: #{candidate.name}
            Current Role: #{candidate.role_name || 'N/A'}
            Current Company: #{candidate.current_company || 'N/A'}
            Location: #{[ candidate.city, candidate.state ].compact.join(', ').presence || 'N/A'}
            Position Level: #{candidate.position_level || 'N/A'}
            Total Experience: #{safe_experience_years(candidate)} years

            Recent Experiences:
            #{exp_summary.presence || '(no experiences)'}

            Education:
            #{edu_summary.presence || '(no education)'}

            Summary:
            #{candidate.curriculum_text&.truncate(600) || candidate.self_introduction&.truncate(400) || '(no summary)'}
          PROFILE
        end.join("\n\n---\n\n")
      end

      def call_llm_with_timeout(profiles_context)
        Timeout.timeout(TIMEOUT_SECONDS) do
          call_llm(profiles_context)
        end
      rescue Timeout::Error
        Rails.logger.warn("[ProfileSynthesizer] LLM timeout after #{TIMEOUT_SECONDS}s")
        nil
      end

      def call_llm(profiles_context)
        Llm::Gateway.fast_chat(
          messages: [
            { role: "system", content: system_prompt },
            { role: "user", content: profiles_context }
          ],
          temperature: 0.2,
          max_tokens: 800,
          response_format: { type: "json_object" },
          tracking: { operation: "similar_candidates.profile_synthesis" }
        )
      end

      def system_prompt
        <<~PROMPT
          You are an expert technical recruiter. Analyze the candidate profiles provided and synthesize an optimized search query to find SIMILAR professionals.

          Your goal is to capture the ESSENCE of these profiles, not copy them literally.

          ## Output Format (JSON ONLY):
          {
            "query": "optimized search query text (max 200 chars, no location)",
            "custom_filters": {
              "locations": ["city, state"] or [],
              "keywords": ["skill1", "skill2", "skill3"],
              "titles": ["role1", "role2"],
              "min_total_experience_years": number or null,
              "industries": ["industry1"] or [],
              "languages": ["language"] or []
            },
            "explanation": "1-sentence summary of synthesized profile"
          }

          ## Rules:
          1. Query: Extract core skills, technologies, domain expertise - NOT company names or people names
          2. Keywords: Focus on technical skills, methodologies, tools that appear across profiles
          3. Titles: Include role variations in PT and EN (e.g., "Tech Lead", "Líder Técnico")
          4. Location: If all profiles are from same city/state, include it. Otherwise leave empty
          5. Experience: Use average/median if profiles vary. Use minimum if consistent
          6. Industries: Only include if clearly relevant to ALL profiles
          7. Languages: Include if explicitly mentioned (usually Portuguese for Brazilian profiles)
          8. Focus on COMMON patterns across profiles, not individual details
          9. Avoid company names - they introduce bias
          10. Keep query concise and search-engine friendly

          ## Examples:

          Example 1 - Single Senior Ruby Developer:
          {
            "query": "senior ruby rails developer backend microservices postgresql",
            "custom_filters": {
              "locations": ["São Paulo, SP"],
              "keywords": ["Ruby", "Rails", "PostgreSQL", "Redis", "Docker", "AWS"],
              "titles": ["Senior Developer", "Tech Lead", "Backend Developer"],
              "min_total_experience_years": 5,
              "industries": ["fintech", "technology"],
              "languages": ["Portuguese"]
            },
            "explanation": "Senior backend developer specialized in Ruby/Rails with cloud infrastructure experience"
          }

          Example 2 - Multiple Mid-Level Frontend Developers:
          {
            "query": "frontend developer react typescript javascript ui/ux",
            "custom_filters": {
              "locations": [],
              "keywords": ["React", "TypeScript", "JavaScript", "HTML", "CSS", "Next.js"],
              "titles": ["Frontend Developer", "Full Stack Developer", "Software Engineer"],
              "min_total_experience_years": 3,
              "industries": [],
              "languages": ["Portuguese"]
            },
            "explanation": "Mid-level frontend developers with modern JavaScript framework experience"
          }

          Example 3 - Sales Executives:
          {
            "query": "enterprise sales executive B2B SaaS account management",
            "custom_filters": {
              "locations": [],
              "keywords": ["Sales", "B2B", "SaaS", "Account Management", "Negotiation"],
              "titles": ["Sales Executive", "Account Executive", "Business Development"],
              "min_total_experience_years": 4,
              "industries": ["technology", "software"],
              "languages": ["Portuguese", "English"]
            },
            "explanation": "Experienced B2B sales professionals with SaaS product expertise"
          }

          Return ONLY valid JSON. No markdown, no explanations outside JSON structure.
        PROMPT
      end

      def parse_and_validate(response, base_candidates)
        parsed = JSON.parse(response.to_s)

        {
          query: parsed["query"]&.strip.presence || build_fallback_query(base_candidates),
          custom_filters: normalize_custom_filters(parsed["custom_filters"] || {}),
          explanation: parsed["explanation"]&.strip.presence || "Similar professionals",
          synthesis_method: "llm"
        }
      rescue JSON::ParserError => e
        Rails.logger.error("[ProfileSynthesizer] JSON parse error: #{e.message}")
        default_synthesis
      end

      def normalize_custom_filters(filters)
        return {} unless filters.is_a?(Hash)

        {}.tap do |normalized|
          normalized[:locations] = Array(filters["locations"] || filters[:locations]).compact if filters["locations"] || filters[:locations]
          normalized[:keywords] = Array(filters["keywords"] || filters[:keywords]).compact.first(10) if filters["keywords"] || filters[:keywords]
          normalized[:titles] = Array(filters["titles"] || filters[:titles]).compact.first(6) if filters["titles"] || filters[:titles]
          normalized[:industries] = Array(filters["industries"] || filters[:industries]).compact if filters["industries"] || filters[:industries]
          normalized[:languages] = Array(filters["languages"] || filters[:languages]).compact if filters["languages"] || filters[:languages]

          min_exp = filters["min_total_experience_years"] || filters[:min_total_experience_years]
          normalized[:min_total_experience_years] = min_exp.to_i if min_exp && min_exp.to_i.positive?
        end
      end

      def safe_experience_years(candidate)
        return "N/A" unless candidate.respond_to?(:total_experience_years)

        candidate.total_experience_years || "N/A"
      end

      def build_fallback_query(candidates)
        roles = candidates.map(&:role_name).compact.uniq.first(2)
        companies = candidates.map(&:current_company).compact.uniq.first(2)

        parts = []
        parts << roles.join(" ") if roles.any?
        parts << "professional" if parts.empty?

        parts.join(" ").truncate(150)
      end

      def default_synthesis
        {
          query: "experienced professional",
          custom_filters: {
            locations: [ "Brasil" ],
            languages: [ "Portuguese" ]
          },
          explanation: "General professional search (fallback)",
          synthesis_method: "fallback"
        }
      end
    end
  end
end
