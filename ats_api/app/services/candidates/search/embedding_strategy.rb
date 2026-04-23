module Candidates
  module Search
    class EmbeddingStrategy
      def initialize(account_id:)
        @account_id = account_id
        @base_filters = BaseFilters.new(account_id: account_id)
      end

      def search(query_embedding, user_filters: {}, pool_size: Configuration.initial_pool_size)
        return [] unless query_embedding

        pre_filtered_ids = apply_pre_filters(user_filters)

        if pre_filtered_ids.present?

          embedding_results = Embedding
            .for_candidates
            .where(reference_id: pre_filtered_ids)
            .nearest_neighbors(:embedding, query_embedding, distance: "cosine")
            .limit(pool_size * 2)
        else
          embedding_results = Embedding
            .for_candidates
            .nearest_neighbors(:embedding, query_embedding, distance: "cosine")
            .limit(pool_size * 2)
        end

        # Filtrar por similaridade mínima: descarta matches fracos (distância cosine alta)
        max_dist = Configuration.embedding_max_distance
        embedding_results = embedding_results.to_a.select { |e| e.neighbor_distance <= max_dist } if max_dist.present?

        candidate_ids = embedding_results.map(&:reference_id).uniq
        return [] if candidate_ids.empty?

        scope = @base_filters.base_scope(Candidate).where(id: candidate_ids)
        scope = scope.where.not(curriculum_text: [ nil, "" ]) if Configuration.require_curriculum_text?

        remaining_filters = user_filters.dup
        remaining_filters.delete(:previous_experiences)
        remaining_filters.delete("previous_experiences")
        remaining_filters.delete(:sectors_a)
        remaining_filters.delete("sectors_a")

        scope = apply_whitelisted_filters(scope, remaining_filters)
        allowed_ids = scope.pluck(:id).to_set

        ordered_ids = embedding_results
          .map(&:reference_id)
          .uniq
          .select { |id| allowed_ids.include?(id) }
          .first(pool_size)

        distances = embedding_results.each_with_object({}) do |e, h|
          h[e.reference_id] = e.neighbor_distance unless h.key?(e.reference_id)
        end

        ordered_ids.each_with_index.map do |id, idx|
          { id: id, rank: idx + 1, distance: distances[id], source: :embedding }
        end
      rescue => e
        Rails.logger.error("[EmbeddingStrategy] Failed: #{e.message}")
        []
      end

      private

      def apply_pre_filters(user_filters)
        restrictive_filters = [ :previous_experiences, :sectors_a ]

        has_restrictive = restrictive_filters.any? { |f| user_filters[f].present? || user_filters[f.to_s].present? }
        return nil unless has_restrictive

        scope = @base_filters.base_scope(Candidate)

        if user_filters[:previous_experiences].present? || user_filters["previous_experiences"].present?
          occupation_names = user_filters[:previous_experiences] || user_filters["previous_experiences"]
          scope = apply_previous_experiences_filter(scope, occupation_names)
        end

        if user_filters[:sectors_a].present? || user_filters["sectors_a"].present?
          sector_names = user_filters[:sectors_a] || user_filters["sectors_a"]
          scope = apply_sectors_filter(scope, sector_names)
        end

        scope.pluck(:id)
      end

      def apply_whitelisted_filters(scope, user_filters)
        normalized_filters = normalize_job_titles_filter(user_filters)

        allowed = FilterMerger.whitelist_for_pgvector(normalized_filters)

        allowed.each do |field, value|
          scope = apply_filter(scope, field, value)
        end

        scope
      end

      def normalize_job_titles_filter(filters)
        job_titles = filters[:current_job_titles] || filters["current_job_titles"]
        return filters unless job_titles.present?

        scope = filters[:current_job_title_scope] || filters["current_job_title_scope"] || "current_and_history"

        result = filters.dup
        result.delete(:current_job_titles)
        result.delete("current_job_titles")
        result.delete(:current_job_title_scope)
        result.delete("current_job_title_scope")

        titles_array = Array(job_titles).map { |t| t.to_s.strip.downcase }.reject(&:blank?)
        return result if titles_array.empty?

        if scope == "current"
          result[:role_name] = titles_array
        else
          result[:experiences_a] = titles_array
        end

        result
      end

      def apply_filter(scope, field, value)
        case field.to_sym
        when :city, :state, :country
          scope.where(field => normalize_location(value))
        when :remote_work
          scope.where(remote_work: value)
        when :position_level
          scope.where(position_level: value)
        when :years_of_experience_min
          scope.where("years_of_experience >= ?", value)
        when :years_of_experience_max
          scope.where("years_of_experience <= ?", value)
        when :current_role_time_min
          apply_current_role_time_min_filter(scope, value)
        when :current_role_time_max
          apply_current_role_time_max_filter(scope, value)
        when :average_time_in_companies_min
          apply_average_time_in_companies_min_filter(scope, value)
        when :average_time_in_companies_max
          apply_average_time_in_companies_max_filter(scope, value)
        when :role_name
          apply_role_name_filter(scope, value)
        when :experiences_a
          apply_experiences_filter(scope, value)
        when :sectors_a
          apply_sectors_filter(scope, value)
        else
          scope
        end
      end

      def apply_role_name_filter(scope, role_names)
        role_names = Array(role_names).map { |n| n.to_s.strip.downcase }.reject(&:blank?)
        return scope if role_names.empty?

        scope.where("LOWER(role_name) IN (?)", role_names)
      end

      def apply_experiences_filter(scope, occupation_names)
        occupation_names = Array(occupation_names).map { |n| n.to_s.strip.downcase }.reject(&:blank?)
        return scope if occupation_names.empty?

        scope
          .joins(experiences: :occupation)
          .where("LOWER(occupations.name) IN (?)", occupation_names)
          .distinct
      end

      def apply_sectors_filter(scope, sector_names)
        sector_names = Array(sector_names).map { |n| n.to_s.strip.downcase }.reject(&:blank?)
        return scope if sector_names.empty?

        result_scope = scope
          .joins(sector_relationships: :sector)
          .where("LOWER(sectors.name) IN (?)", sector_names)
          .where(sector_relationships: { is_deleted: false })
          .distinct

        result_scope
      end

      def normalize_location(value)
        return value if value.is_a?(Array)
        value.to_s.downcase.strip
      end

      def apply_current_role_time_min_filter(scope, min_months)
        scope
          .joins(:experiences)
          .where(experiences: { work_here: true })
          .where(
            "(EXTRACT(YEAR FROM AGE(NOW(), experiences.start_date)) * 12 + EXTRACT(MONTH FROM AGE(NOW(), experiences.start_date))) >= ?",
            min_months.to_i
          )
          .distinct
      end

      def apply_current_role_time_max_filter(scope, max_months)
        scope
          .joins(:experiences)
          .where(experiences: { work_here: true })
          .where(
            "(EXTRACT(YEAR FROM AGE(NOW(), experiences.start_date)) * 12 + EXTRACT(MONTH FROM AGE(NOW(), experiences.start_date))) <= ?",
            max_months.to_i
          )
          .distinct
      end

      def apply_average_time_in_companies_min_filter(scope, min_months)
        candidate_ids = scope.select(:id).map do |candidate|
          avg_time = calculate_average_time_in_companies_for_candidate(candidate.id)
          candidate.id if avg_time && avg_time >= min_months.to_i
        end.compact

        scope.where(id: candidate_ids)
      end

      def apply_average_time_in_companies_max_filter(scope, max_months)
        candidate_ids = scope.select(:id).map do |candidate|
          avg_time = calculate_average_time_in_companies_for_candidate(candidate.id)
          candidate.id if avg_time && avg_time <= max_months.to_i
        end.compact

        scope.where(id: candidate_ids)
      end

      def calculate_average_time_in_companies_for_candidate(candidate_id)
        result = ActiveRecord::Base.connection.execute(<<~SQL)
          SELECT#{' '}
            AVG(company_duration) as avg_months
          FROM (
            SELECT#{' '}
              company_id,
              SUM(
                (EXTRACT(YEAR FROM AGE(COALESCE(end_date, NOW()), start_date)) * 12 +#{' '}
                 EXTRACT(MONTH FROM AGE(COALESCE(end_date, NOW()), start_date)))
              ) as company_duration
            FROM experiences
            WHERE candidate_id = #{candidate_id}
              AND start_date IS NOT NULL
            GROUP BY company_id
            HAVING SUM(
              (EXTRACT(YEAR FROM AGE(COALESCE(end_date, NOW()), start_date)) * 12 +#{' '}
               EXTRACT(MONTH FROM AGE(COALESCE(end_date, NOW()), start_date)))
            ) > 0
          ) as company_durations
        SQL

        result.first&.dig("avg_months")&.to_f&.round
      end

      def apply_previous_experiences_filter(scope, occupation_names)
        occupation_names = Array(occupation_names).map { |n| n.to_s.strip.downcase }.reject(&:blank?)
        return scope if occupation_names.empty?

        result_scope = scope
          .joins(experiences: :occupation)
          .where("LOWER(occupations.name) IN (?)", occupation_names)
          .where("experiences.work_here != ? OR experiences.work_here IS NULL", true)
          .distinct

        result_scope
      end
    end
  end
end
