# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class IntentBasedRefinementService
      GAMMA = 0.25
      MAX_SKILLS_TO_EXTRACT = 15
      MAX_SKILLS_TO_SHOW = 8

      IntentResult = Struct.new(
        :embedding, :description, :elasticsearch_query,
        :must_have_skills, :nice_to_have_skills,
        :searchable_attributes, :not_searchable_feedback,
        :skipped, keyword_init: true
      )

      def initialize(encoder: nil)
        @encoder = encoder || Embeddings::Encoder.new
      end

      def refine_with_intent(
        original_centroid:,
        vectorial_refined:,
        base_candidates:,
        disliked_feedbacks:,
        liked_candidates: []
      )
        if disliked_feedbacks.empty?
          return IntentResult.new(
            embedding: vectorial_refined,
            skipped: true
          )
        end

        extraction = extract_intent(
          base_candidates: base_candidates,
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: liked_candidates
        )

        unless extraction
          return IntentResult.new(
            embedding: vectorial_refined,
            skipped: true
          )
        end

        description = extraction[:ideal_candidate_description]
        if description.blank?
          return IntentResult.new(
            embedding: vectorial_refined,
            not_searchable_feedback: extraction[:not_searchable_feedback],
            skipped: true
          )
        end

        log_extracted_intent(description)

        intent_embedding = generate_embedding(description)
        unless intent_embedding
          return IntentResult.new(
            embedding: vectorial_refined,
            skipped: true
          )
        end

        IntentResult.new(
          embedding: blend_embeddings(vectorial_refined, intent_embedding),
          description: description,
          elasticsearch_query: extraction[:elasticsearch_query],
          must_have_skills: extraction[:must_have_skills],
          nice_to_have_skills: extraction[:nice_to_have_skills],
          searchable_attributes: extraction[:searchable_attributes],
          not_searchable_feedback: extraction[:not_searchable_feedback],
          skipped: false
        )
      rescue => e
        log_refinement_failure(e)
        IntentResult.new(embedding: vectorial_refined, skipped: true)
      end

      private

      def extract_intent(base_candidates:, disliked_feedbacks:, liked_candidates:)
        prompt = build_extraction_prompt(
          base_candidates: base_candidates,
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: liked_candidates
        )

        response = call_llm(prompt)
        parse_structured_response(response)
      rescue => e
        log_extraction_failure(e)
        nil
      end

      def call_llm(prompt)
        Llm::Gateway.fast_chat(
          messages: [
            { role: "system", content: system_prompt },
            { role: "user", content: prompt }
          ],
          temperature: 0.2,
          max_tokens: 4096,
          tracking: { operation: "similar_candidates.intent_refinement" }
        )
      end

      def parse_structured_response(response)
        content = response.dig("choices", 0, "message", "content")
        return nil unless content

        json_match = content.match(/\{.*\}/m)
        return nil unless json_match

        parsed = JSON.parse(json_match[0])

        description = parsed["ideal_candidate_description"].to_s.strip
        es_query = parsed["elasticsearch_query"].to_s.strip
        must_have = Array(parsed["must_have_skills"])
        nice_to_have = Array(parsed["nice_to_have_skills"])
        searchable = Array(parsed["searchable_attributes"])
        not_searchable = Array(parsed["not_searchable_feedback"])

        if description.blank? && searchable.empty?
          log_all_not_searchable(not_searchable)
          return {
            ideal_candidate_description: nil,
            elasticsearch_query: nil,
            must_have_skills: [],
            nice_to_have_skills: [],
            searchable_attributes: [],
            not_searchable_feedback: not_searchable
          }
        end

        {
          ideal_candidate_description: description.presence,
          elasticsearch_query: es_query.presence,
          must_have_skills: must_have,
          nice_to_have_skills: nice_to_have,
          searchable_attributes: searchable,
          not_searchable_feedback: not_searchable
        }
      rescue JSON::ParserError => e
        Rails.logger.warn "[IntentRefinement] JSON parse failed, using raw content"
        {
          ideal_candidate_description: content&.strip,
          elasticsearch_query: nil,
          must_have_skills: [],
          nice_to_have_skills: [],
          searchable_attributes: [],
          not_searchable_feedback: []
        }
      end

      def system_prompt
        <<~PROMPT
          You are a recruiter intent analyzer. Your job is to understand what the recruiter WANTS based on who they rejected and why.

          SEMANTIC RULES:
          - "não sabe X" / "nao sabe X" → recruiter WANTS X
          - "não conhece Y" → recruiter WANTS Y
          - "muito junior" / "pouca experiência" → recruiter WANTS more seniority
          - "não fala X" / "X fraco" → recruiter WANTS fluency in language X
          - "nunca foi Y" / "sem perfil de Y" → recruiter WANTS Y experience
          - "precisa de Z" → recruiter explicitly WANTS Z

          CLASSIFICATION RULES — classify each feedback as:
          - SEARCHABLE: skills, programming languages, spoken languages, seniority level,
            leadership experience, domain expertise, tech stack, industry background,
            certifications, education level — things that appear in resumes/CVs
          - NOT_SEARCHABLE: salary expectations, travel availability, work model
            (remote/onsite/PJ/CLT), cultural fit, personal availability, relocation
            willingness, notice period, subjective opinions ("não gostei", "sem fit")

          IMPORTANT — CONTEXTUALIZED SEARCH:
          The recruiter started with specific base candidates. The elasticsearch_query
          MUST combine the base profile (existing skills/role) with the desired improvements.
          Do NOT search only for the new skills — that would return unrelated candidates.
          Example: base is Java/Spring, dislike "não sabe ruby" → query MUST be
          "Java Spring Ruby Rails backend senior", NOT just "ruby rails".

          Output ONLY valid JSON:
          {
            "ideal_candidate_description": "Description combining base profile + desired improvements. If ALL feedback is not_searchable, set to empty string.",
            "elasticsearch_query": "Contextualized search query combining base profile skills + desired skills. Example: 'Java Spring Ruby Rails backend senior'. If ALL feedback is not_searchable, set to empty string.",
            "must_have_skills": ["ruby", "rails"],
            "nice_to_have_skills": ["java", "spring", "aws"],
            "searchable_attributes": ["ruby", "english", "senior"],
            "not_searchable_feedback": [
              {"feedback": "pretensão muito alta", "type": "salary"},
              {"feedback": "não aceita PJ", "type": "work_model"}
            ]
          }
        PROMPT
      end

      def build_extraction_prompt(base_candidates:, disliked_feedbacks:, liked_candidates:)
        <<~PROMPT
          BASE CANDIDATES (recruiter started search with these):
          #{format_candidates(base_candidates)}

          REJECTED CANDIDATES (with reasons):
          #{format_disliked_feedbacks(disliked_feedbacks)}

          LIKED CANDIDATES:
          #{format_liked_candidates(liked_candidates)}

          Based on this feedback:
          1. Describe the IDEAL candidate combining the base profile with desired improvements.
          2. Generate an elasticsearch_query that combines base skills + desired skills (NOT just new skills alone).
          3. List must_have_skills (skills the recruiter explicitly wants) and nice_to_have_skills (skills from base profile).
          4. Classify each feedback as SEARCHABLE or NOT_SEARCHABLE.
          5. If ALL feedback is not_searchable, set ideal_candidate_description and elasticsearch_query to "".
          Be specific and concise (max 2 sentences for description).
        PROMPT
      end

      def format_candidates(candidates)
        return "(none)" if candidates.empty?

        candidates.map { |c| format_candidate_with_skills(c) }.join("\n")
      end

      def format_disliked_feedbacks(feedbacks)
        feedbacks.map do |df|
          candidate = df[:candidate] || Candidate.find_by(id: df[:candidate_id])
          "- #{candidate&.name}: \"#{df[:reason]}\""
        end.join("\n")
      end

      def format_liked_candidates(candidates)
        return "(none)" if candidates.empty?

        candidates.map { |c| format_candidate_with_skills(c) }.join("\n")
      end

      def format_candidate_with_skills(candidate)
        skills = extract_candidate_skills(candidate)
        skill_info = skills.any? ? " (skills: #{skills.take(MAX_SKILLS_TO_SHOW).join(', ')})" : ""
        "- #{candidate.name}: #{candidate.role_name || 'N/A'}#{skill_info}"
      end

      def generate_embedding(description)
        @encoder.call(description)
      rescue => e
        Rails.logger.error "[IntentRefinement] Embedding generation failed: #{e.message}"
        nil
      end

      def blend_embeddings(vectorial_refined, intent_embedding)
        return vectorial_refined if intent_embedding.blank?

        vec_normalized = normalize(vectorial_refined)
        intent_normalized = normalize(intent_embedding)

        blended = blend_vectors(vec_normalized, intent_normalized)
        normalize(blended)
      end

      def blend_vectors(vec1, vec2)
        dims = vec1.size
        Array.new(dims) { |i| (1 - GAMMA) * vec1[i] + GAMMA * vec2[i] }
      end

      def normalize(vector)
        magnitude = compute_magnitude(vector)
        return vector if magnitude.zero?

        vector.map { |v| v / magnitude }
      end

      def compute_magnitude(vector)
        Math.sqrt(vector.sum { |v| v**2 })
      end

      def extract_candidate_skills(candidate)
        skills = []
        skills.concat(extract_skills_from_data_raw(candidate))
        skills.concat(extract_skills_from_curriculum(candidate))
        skills.uniq.compact.take(MAX_SKILLS_TO_EXTRACT)
      end

      def extract_skills_from_data_raw(candidate)
        return [] unless candidate.respond_to?(:data_raw) && candidate.data_raw.is_a?(Hash)

        raw_skills = candidate.data_raw.dig("skills") || []
        raw_skills.map { |s| s.is_a?(Hash) ? s["name"] : s }.compact
      end

      def extract_skills_from_curriculum(candidate)
        return [] unless candidate.respond_to?(:curriculum_text) && candidate.curriculum_text.present?

        text = candidate.curriculum_text.downcase
        common_skills.select { |skill| text.include?(skill) }
      end

      def common_skills
        @common_skills ||= %w[
          ruby rails python java javascript typescript react vue angular node
          spring django flask express api rest graphql sql postgresql mysql
          mongodb redis docker kubernetes aws azure gcp terraform ansible
          git jenkins circleci agile scrum kanban
        ]
      end

      def log_extracted_intent(description)
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "🧠 [IntentRefinement] IDEAL CANDIDATE PROFILE"
        Rails.logger.info "   #{description.truncate(200)}"
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      end

      def log_all_not_searchable(not_searchable)
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "💡 [IntentRefinement] ALL FEEDBACK IS NOT SEARCHABLE"
        Rails.logger.info "   Skipping intent blending — #{not_searchable.size} non-actionable feedbacks"
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      end

      def log_extraction_failure(error)
        Rails.logger.error "[IntentRefinement] LLM extraction failed: #{error.message}"
      end

      def log_refinement_failure(error)
        Rails.logger.error "[IntentRefinement] Failed: #{error.message}"
        Rails.logger.error error.backtrace.first(5).join("\n")
      end
    end
  end
end
