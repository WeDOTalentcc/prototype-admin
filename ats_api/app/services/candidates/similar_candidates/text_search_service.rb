# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class TextSearchService
      DEFAULT_LIMIT = 30
      DEFAULT_FIELDS = [
        "skills^10",
        "curriculum_summary^7",
        "role_name^8",
        "experiences_a^6",
        "recent_roles^6",
        "current_company^4",
        "all_companies^3"
      ].freeze

      def initialize(account_id:)
        @account_id = account_id
      end

      def search(query:, exclude_ids: [], must_have_skills: [], limit: DEFAULT_LIMIT)
        return [] if query.blank?

        search_options = build_search_options(exclude_ids: exclude_ids, limit: limit)

        results = execute_search(query, search_options)
        boost_must_have_skills(results, must_have_skills)
      rescue Searchkick::Error => e
        log_search_error(e)
        []
      rescue => e
        log_unexpected_error(e)
        []
      end

      private

      def build_search_options(exclude_ids:, limit:)
        where_clause = { account_id: @account_id, is_deleted: [ false, nil ] }
        where_clause[:id] = { not: exclude_ids } if exclude_ids.any?

        {
          fields: DEFAULT_FIELDS,
          where: where_clause,
          limit: limit,
          operator: "or",
          misspellings: { below: 3 }
        }
      end

      def execute_search(query, options)
        results = Candidate.search(query, **options)

        results.map.with_index do |candidate, index|
          {
            candidate_id: candidate.id,
            similarity: compute_normalized_score(results, index),
            source: :text
          }
        end
      end

      def compute_normalized_score(results, index)
        return 0.0 if results.empty?

        hit = results.hits[index]
        score = hit["_score"].to_f
        max_score = results.hits.first["_score"].to_f

        return 0.0 if max_score.zero?

        (score / max_score).clamp(0.0, 1.0)
      end

      def boost_must_have_skills(results, must_have_skills)
        return results if must_have_skills.empty?

        candidate_ids = results.map { |r| r[:candidate_id] }
        candidates = Candidate.where(id: candidate_ids, account_id: @account_id).index_by(&:id)

        results.each do |result|
          candidate = candidates[result[:candidate_id]]
          next unless candidate

          match_ratio = skill_match_ratio(candidate, must_have_skills)
          result[:must_have_match] = match_ratio
        end

        results.sort_by { |r| [ -(r[:must_have_match] || 0), -(r[:similarity] || 0) ] }
      end

      def skill_match_ratio(candidate, must_have_skills)
        return 0.0 if must_have_skills.empty?

        structured_skills = extract_structured_skills(candidate)
        searchable_text = build_searchable_text(candidate)

        matched = must_have_skills.count do |skill|
          skill_lower = skill.downcase
          structured_skills.any? { |s| s.include?(skill_lower) } ||
            searchable_text.match?(/\b#{Regexp.escape(skill_lower)}\b/)
        end

        matched.to_f / must_have_skills.size
      end

      def extract_structured_skills(candidate)
        return [] unless candidate.data_raw.is_a?(Hash)

        raw_skills = candidate.data_raw.dig("skills") || []
        raw_skills.map { |s| (s.is_a?(Hash) ? s["name"] : s.to_s).downcase }
      end

      def build_searchable_text(candidate)
        parts = []
        parts << candidate.curriculum_text if candidate.curriculum_text.present?
        parts << candidate.role_name if candidate.role_name.present?

        if candidate.data_raw.is_a?(Hash)
          raw_skills = candidate.data_raw.dig("skills") || []
          raw_skills.each do |s|
            parts << (s.is_a?(Hash) ? s["name"] : s.to_s)
          end
        end

        parts.join(" ").downcase
      end

      def log_search_error(error)
        Rails.logger.error "[TextSearch] Searchkick error: #{error.message}"
      end

      def log_unexpected_error(error)
        Rails.logger.error "[TextSearch] Failed: #{error.message}"
        Rails.logger.error error.backtrace.first(5).join("\n")
      end
    end
  end
end
