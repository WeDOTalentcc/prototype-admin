module Candidates
  module Search
    class MultiQueryGenerator
      Result = Struct.new(:queries, :weights, :strategy_used, keyword_init: true)

      def generate(profile, context: :resume)
        return build_empty_result if profile.blank?

        queries = build_queries_from_profile(profile, context)
        weights = calculate_weights(queries.size)

        Result.new(
          queries: queries,
          weights: weights,
          strategy_used: :profile_based
        )
      end

      private

      def build_queries_from_profile(profile, context)
        queries = []

        role_query = build_role_focused_query(profile)
        queries << role_query if role_query.present?

        tech_query = build_tech_focused_query(profile)
        queries << tech_query if tech_query.present?

        industry_query = build_industry_focused_query(profile)
        queries << industry_query if industry_query.present?

        experience_query = build_experience_focused_query(profile)
        queries << experience_query if experience_query.present?

        hybrid_query = build_hybrid_query(profile)
        queries << hybrid_query if hybrid_query.present?

        queries.compact.uniq.first(5)
      end

      def build_role_focused_query(profile)
        parts = []
        parts << profile["seniority"] if profile["seniority"].present?
        parts << profile["primary_role"] if profile["primary_role"].present?

        return nil if parts.empty?

        parts.join(" ")
      end

      def build_tech_focused_query(profile)
        techs = Array(profile["core_technologies"])
        return nil if techs.empty?

        techs.first(4).join(" ")
      end

      def build_industry_focused_query(profile)
        parts = []
        parts << profile["primary_role"] if profile["primary_role"].present?
        parts << profile["industry"] if profile["industry"].present?

        skills = Array(profile["transferable_skills"])
        parts << skills.first if skills.any?

        return nil if parts.size < 2

        parts.join(" ")
      end

      def build_experience_focused_query(profile)
        parts = []
        parts << profile["seniority"] if profile["seniority"].present?

        if profile["years_experience"].present?
          parts << "#{profile['years_experience']} anos"
        end

        parts << profile["primary_role"] if profile["primary_role"].present?

        return nil if parts.size < 2

        parts.join(" ")
      end

      def build_hybrid_query(profile)
        techs = Array(profile["core_technologies"])
        role = profile["primary_role"]

        return nil if techs.empty? || role.blank?

        "#{techs.first(2).join(' ')} #{role}"
      end

      def calculate_weights(count)
        return [] if count == 0

        base_weights = [ 0.3, 0.25, 0.2, 0.15, 0.1 ]
        weights = base_weights.first(count)

        total = weights.sum
        weights.map { |w| (w / total).round(2) }
      end

      def build_empty_result
        Result.new(
          queries: [],
          weights: [],
          strategy_used: :empty
        )
      end
    end
  end
end
