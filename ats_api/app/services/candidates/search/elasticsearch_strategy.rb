module Candidates
  module Search
    class ElasticsearchStrategy
      QUERY_STOPWORDS = %w[
        a as o os um uma de da das do dos e ou com sem para por em no na nos nas
        the and or with without for in on at to from
        busca buscar procure procurando candidato candidatos vaga vagas perfil perfis
        experiencia experiencias experiência experiências anos ano meses mes
      ].freeze

      def initialize(account_id:)
        @account_id = account_id
        @base_filters = BaseFilters.new(account_id: account_id)
      end

      def search(query, user_filters: {}, pool_size: Configuration.initial_pool_size)
        safe_filters = FilterMerger.merge(@base_filters.to_hash, user_filters)
        safe_filters = apply_years_of_experience_range(safe_filters)
        safe_filters = apply_current_role_time_range(safe_filters)
        safe_filters = apply_average_time_in_companies_range(safe_filters)
        safe_filters = apply_current_job_titles_filter(safe_filters)
        safe_filters = apply_previous_experiences_filter(safe_filters)
        safe_filters = apply_experiences_filter(safe_filters)
        safe_filters = apply_sectors_filter(safe_filters)
        safe_filters = apply_companies_filter(safe_filters)
        safe_filters = apply_company_sectors_filter(safe_filters)
        safe_filters = apply_universities_filter(safe_filters)
        safe_filters = apply_academic_degree_filter(safe_filters)
        safe_filters = apply_skills_filter(safe_filters)
        safe_filters = apply_skill_categories_filter(safe_filters)
        safe_filters = apply_languages_filter(safe_filters)
        study_areas_context = extract_study_areas_filter(safe_filters)
        safe_filters = remove_study_areas_from_filters(safe_filters)
        excluded_companies_filters = extract_excluded_companies_filter(safe_filters)
        safe_filters = remove_excluded_companies_from_filters(safe_filters)

        search_query = query.presence || "*"

        has_occupation_filter = safe_filters[:experiences_a].present? || safe_filters[:role_name].present?
        effective_query = has_occupation_filter ? "*" : search_query

        query_context = build_query_context(effective_query)
        threshold = calculate_threshold(effective_query, query_context)
        search_operator = select_search_operator(effective_query, query_context)

        Rails.logger.info("[ESStrategy] Query: #{search_query.to_s.truncate(100)}")

        search_fields = effective_query == "*" ? nil : [
          "experiences_a^7",        # TODAS as ocupações - peso alto
          "curriculum_text^5",
          "role_name^3",
          "recent_roles^3",         # Cargos recentes
          "name^2",
          "current_company^2",
          "self_introduction"
        ]

        search_options = {
          where: safe_filters,
          per_page: pool_size,
          order: { _score: :desc },
          load: false,
          operator: search_operator
        }

        search_options[:fields] = search_fields if search_fields.present?

        body_options = {}

        if effective_query != "*"
          body_options[:query] = {
            bool: {
              minimum_should_match: threshold
            }
          }
        end

        if excluded_companies_filters.present?
          body_options[:query] ||= { bool: {} }
          body_options[:query][:bool][:must_not] = build_excluded_companies_clauses(excluded_companies_filters)
        end

        if study_areas_context.present?
          body_options[:query] ||= { bool: {} }
          body_options[:query][:bool][:filter] ||= []
          body_options[:query][:bool][:filter] << build_study_areas_clause(study_areas_context)
        end

        search_options[:body_options] = body_options if body_options.present?

        results = Candidate.search(effective_query, **search_options)

        extracted = extract_results_with_score(results)

        extracted
      rescue Searchkick::Error => e
        Rails.logger.error("[ESStrategy] Searchkick error: #{e.message}")
        []
      rescue => e
        Rails.logger.error("[ESStrategy] Failed: #{e.message}")
        Rails.logger.error(e.backtrace.first(5).join("\n"))
        []
      end

      private

      def apply_years_of_experience_range(filters)
        result = filters.dup

        if filters[:years_of_experience_min].present? || filters[:years_of_experience_max].present?
          range = {}
          range[:gte] = filters[:years_of_experience_min].to_i if filters[:years_of_experience_min].present?
          range[:lte] = filters[:years_of_experience_max].to_i if filters[:years_of_experience_max].present?

          result[:years_of_experience] = range
          result.delete(:years_of_experience_min)
          result.delete(:years_of_experience_max)
        end

        result
      end

      def apply_current_role_time_range(filters)
        result = filters.dup

        if filters[:current_role_time_min].present? || filters[:current_role_time_max].present?
          range = {}
          range[:gte] = filters[:current_role_time_min].to_i if filters[:current_role_time_min].present?
          range[:lte] = filters[:current_role_time_max].to_i if filters[:current_role_time_max].present?

          result[:current_role_time] = range
          result.delete(:current_role_time_min)
          result.delete(:current_role_time_max)
        end

        result
      end

      def apply_average_time_in_companies_range(filters)
        result = filters.dup

        if filters[:average_time_in_companies_min].present? || filters[:average_time_in_companies_max].present?
          range = {}
          range[:gte] = filters[:average_time_in_companies_min].to_i if filters[:average_time_in_companies_min].present?
          range[:lte] = filters[:average_time_in_companies_max].to_i if filters[:average_time_in_companies_max].present?

          result[:average_time_in_companies] = range
          result.delete(:average_time_in_companies_min)
          result.delete(:average_time_in_companies_max)
        end

        result
      end

      def apply_current_job_titles_filter(filters)
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
          result[:role_name] = titles_array.size == 1 ? titles_array.first : titles_array
        else
          result[:experiences_a] = titles_array.size == 1 ? titles_array.first : titles_array
        end

        result
      end

      def apply_experiences_filter(filters)
        experiences = filters[:experiences_a] || filters["experiences_a"]
        return filters unless experiences.present?

        result = filters.dup

        experiences_array = Array(experiences).map { |t| t.to_s.strip.downcase }.reject(&:blank?)

        return result if experiences_array.empty?

        result[:experiences_a] = experiences_array.size == 1 ? experiences_array.first : experiences_array

        result
      end

      def apply_previous_experiences_filter(filters)
        previous = filters[:previous_experiences] || filters["previous_experiences"]
        return filters unless previous.present?

        result = filters.dup

        previous_array = Array(previous).map { |t| t.to_s.strip.downcase }.reject(&:blank?)

        return result if previous_array.empty?

        result[:previous_experiences] = previous_array.size == 1 ? previous_array.first : previous_array

        result
      end

      def apply_sectors_filter(filters)
        sectors = filters[:sectors_a] || filters["sectors_a"]
        return filters unless sectors.present?

        result = filters.dup

        sectors_array = Array(sectors).map { |s| s.to_s.strip.downcase }.reject(&:blank?)

        return result if sectors_array.empty?

        result[:sectors_a] = sectors_array.size == 1 ? sectors_array.first : sectors_array

        result
      end

      def apply_companies_filter(filters)
        companies_filter = filters[:companies] || filters["companies"]
        return filters unless companies_filter.present?

        scope = companies_filter[:scope] || companies_filter["scope"] || "current_and_previous"
        values = companies_filter[:values] || companies_filter["values"]

        result = filters.dup
        result.delete(:companies)
        result.delete("companies")

        companies_array = Array(values).map { |c| c.to_s.strip.downcase }.reject(&:blank?)

        return result if companies_array.empty?

        case scope
        when "current_only"
          result[:current_company] = companies_array.size == 1 ? companies_array.first : companies_array
        when "previous_only"
          result[:previous_companies] = companies_array.size == 1 ? companies_array.first : companies_array
        when "current_and_previous"
          result[:all_companies] = companies_array.size == 1 ? companies_array.first : companies_array
        end

        result
      end

      def apply_company_sectors_filter(filters)
        sectors_filter = filters[:company_sectors] || filters["company_sectors"]
        return filters unless sectors_filter.present?

        scope = sectors_filter[:scope] || sectors_filter["scope"] || "current_and_previous"
        values = sectors_filter[:values] || sectors_filter["values"]

        result = filters.dup
        result.delete(:company_sectors)
        result.delete("company_sectors")

        sectors_array = Array(values).map { |s| s.to_s.strip.downcase }.reject(&:blank?)

        return result if sectors_array.empty?

        case scope
        when "current_only"
          result[:current_company_sectors] = sectors_array.size == 1 ? sectors_array.first : sectors_array
        when "current_and_previous"
          result[:all_company_sectors] = sectors_array.size == 1 ? sectors_array.first : sectors_array
        end

        result
      end

      def extract_excluded_companies_filter(filters)
        excluded_filter = filters[:excluded_companies] || filters["excluded_companies"]
        return nil unless excluded_filter.present?

        scope = excluded_filter[:scope] || excluded_filter["scope"] || "current_and_previous"
        values = excluded_filter[:values] || excluded_filter["values"]

        companies_array = Array(values).map { |c| c.to_s.strip.downcase }.reject(&:blank?)

        return nil if companies_array.empty?

        { scope: scope, values: companies_array }
      end

      def remove_excluded_companies_from_filters(filters)
        result = filters.dup
        result.delete(:excluded_companies)
        result.delete("excluded_companies")
        result
      end

      def build_excluded_companies_clauses(excluded_filter)
        companies = excluded_filter[:values]
        scope = excluded_filter[:scope]

        case scope
        when "current_only"
          [ { terms: { current_company: companies } } ]
        when "current_and_previous"
          [ { terms: { all_companies: companies } } ]
        else
          []
        end
      end


      # Calcula threshold baseado no número de palavras da query.
      #
      # Lógica:
      # - Query muito curta (1-2 palavras): precisa ter todas → 100%
      # - Query curta (3-4 palavras): ~2 de 3-4 → 60%
      # - Query média (5-8 palavras): ~2-3 de 5-8 → 40%
      # - Query longa (9-20 palavras): mais permissivo → 25%
      # - Query muito longa (currículo): muito permissivo → 15%
      #
      def calculate_threshold(query, query_context = nil)
        return "1" if query.to_s.strip == "*"

        count = word_count(query)
        is_specific_query = query_context&.dig(:is_specific_query)

        if is_specific_query
          return case count
                 when 1..2
            "100%"
                 when 3..4
            "75%"
                 when 5..8
            "60%"
                 when 9..20
            "50%"
                 else
            "40%"
                 end
        end

        case count
        when 1..2
          "100%"
        when 3..4
          "60%"
        when 5..8
          "50%"
        when 9..20
          "35%"
        else
          "25%"
        end
      end

      def select_search_operator(query, query_context)
        return "or" if query.to_s.strip == "*"

        count = word_count(query)
        return "and" if query_context[:is_specific_query] && count <= 8

        "or"
      end

      def build_query_context(query)
        terms = normalized_query_terms(query)
        significant_terms = extract_significant_terms(terms)

        {
          terms: terms,
          significant_terms: significant_terms,
          is_specific_query: significant_terms.size >= 2
        }
      end

      def normalized_query_terms(query)
        query
          .to_s
          .downcase
          .scan(/[[:alnum:]&]+/)
          .reject(&:blank?)
      end

      def extract_significant_terms(terms)
        terms
          .reject { |term| QUERY_STOPWORDS.include?(term) }
          .reject { |term| term.length <= 2 }
          .uniq
      end

      def apply_universities_filter(filters)
        return filters unless filters[:universities].present?

        universities = Array(filters[:universities]).map(&:downcase)
        filters[:all_institutions] = universities
        filters.except(:universities)
      end

      def extract_study_areas_filter(filters)
        return nil unless filters[:study_areas].present?

        study_areas_param = filters[:study_areas]

        if study_areas_param.is_a?(Hash)
          scope = study_areas_param[:scope] || study_areas_param["scope"] || "regular"
          values = study_areas_param[:values] || study_areas_param["values"] || []
          universities = study_areas_param[:universities] || study_areas_param["universities"] || []

          {
            scope: scope,
            values: Array(values).map(&:downcase),
            universities: Array(universities).map(&:downcase)
          }
        else
          {
            scope: "regular",
            values: Array(study_areas_param).map(&:downcase),
            universities: []
          }
        end
      end

      def remove_study_areas_from_filters(filters)
        filters.except(:study_areas)
      end

      def build_study_areas_clause(context)
        scope = context[:scope]
        values = context[:values]
        universities = context[:universities]

        case scope
        when "nested"
          if universities.present?
            {
              bool: {
                must: [
                  { terms: { all_study_areas: values } },
                  { terms: { all_institutions: universities } }
                ]
              }
            }
          else
            { terms: { all_study_areas: values } }
          end
        else
          { terms: { all_study_areas: values } }
        end
      end

      def apply_academic_degree_filter(filters)
        return filters unless filters[:academic_degree].present?

        academic_degree_param = filters[:academic_degree]

        if academic_degree_param.is_a?(Hash)
          scope = academic_degree_param[:scope] || academic_degree_param["scope"] || "min"
          value = academic_degree_param[:value] || academic_degree_param["value"]

          if value.present?
            normalized_value = normalize_degree_value(value)

            if scope == "min"
              hierarchy = {
                "high school" => 1,
                "technical" => 2,
                "online course" => 3,
                "bachelors" => 4,
                "postgraduate" => 5,
                "masters" => 6,
                "doctorate" => 7,
                "phd" => 8
              }

              min_level = hierarchy[normalized_value]

              if min_level
                valid_levels = hierarchy.select { |_, level| level >= min_level }.keys
                filters[:all_education_levels] = valid_levels
              end
            else
              filters[:all_education_levels] = [ normalized_value ]
            end
          end
        end

        filters.except(:academic_degree)
      end

      def normalize_degree_value(value)
        normalized = value.to_s.strip.downcase

        portuguese_mapping = {
          "ensino médio" => "high school",
          "ensino medio" => "high school",
          "curso técnico" => "technical",
          "curso tecnico" => "technical",
          "técnico" => "technical",
          "tecnico" => "technical",
          "curso online" => "online course",
          "graduação" => "bachelors",
          "graduacao" => "bachelors",
          "pós-graduação" => "postgraduate",
          "pos-graduacao" => "postgraduate",
          "pós graduação" => "postgraduate",
          "pos graduacao" => "postgraduate",
          "mestrado" => "masters",
          "doutorado" => "doctorate",
          "phd" => "phd",
          "outros" => "other"
        }

        portuguese_mapping[normalized] || normalized
      end

      def apply_skills_filter(filters)
        return filters unless filters[:skills].present?

        skills_param = filters[:skills]
        mandatory_skills = []

        if skills_param.is_a?(Array)
          skills_param.each do |skill|
            if skill.is_a?(Hash)
              name = skill[:name] || skill["name"]
              is_mandatory = skill[:isMandatory] || skill["isMandatory"] || false

              mandatory_skills << name.to_s.downcase if is_mandatory && name.present?
            else
              mandatory_skills << skill.to_s.downcase if skill.present?
            end
          end
        end

        filters[:skills] = mandatory_skills if mandatory_skills.present?

        filters
      end

      def apply_skill_categories_filter(filters)
        return filters unless filters[:skill_categories].present?

        categories_param = filters[:skill_categories]
        category_names = []

        if categories_param.is_a?(Array)
          categories_param.each do |category|
            if category.is_a?(Hash)
              name = category[:name] || category["name"]
              category_names << name.to_s.downcase if name.present?
            else
              category_names << category.to_s.downcase if category.present?
            end
          end
        end

        filters[:skill_categories] = category_names if category_names.present?

        filters
      end

      def apply_languages_filter(filters)
        return filters unless filters[:languages].present?

        languages_param = filters[:languages]
        languages_with_proficiency = []
        languages_only = []

        if languages_param.is_a?(Array)
          languages_param.each do |lang|
            if lang.is_a?(Hash)
              name = lang[:name] || lang["name"]
              proficiency = lang[:proficiency] || lang["proficiency"]

              if name.present?
                normalized_name = name.to_s.downcase

                if proficiency.present? && proficiency.to_s.strip != ""
                  normalized_proficiency = normalize_proficiency_for_search(proficiency)
                  languages_with_proficiency << "#{normalized_name}:#{normalized_proficiency}"
                else
                  languages_only << normalized_name
                end
              end
            else
              languages_only << lang.to_s.downcase if lang.present?
            end
          end
        end

        filters[:languages_with_proficiency] = languages_with_proficiency if languages_with_proficiency.present?
        filters[:languages] = languages_only if languages_only.present?

        filters
      end

      def normalize_proficiency_for_search(proficiency)
        normalized = proficiency.to_s.strip.downcase

        proficiency_mapping = {
          "básico" => "basic",
          "basico" => "basic",
          "intermediário" => "intermediate",
          "intermediario" => "intermediate",
          "avançado" => "advanced",
          "avancado" => "advanced",
          "fluente" => "fluent",
          "nativo" => "native"
        }

        proficiency_mapping[normalized] || normalized
      end

      def word_count(query)
        query.to_s.split(/\s+/).reject(&:blank?).size
      end

      def extract_results_with_score(results)
        hits = results.response.dig("hits", "hits") || []

        hits.map.with_index do |hit, idx|
          {
            id: hit["_id"].to_i,
            rank: idx + 1,
            score: hit["_score"].to_f,
            source: :elasticsearch
          }
        end
      rescue => e
        Rails.logger.warn("[ESStrategy] Fallback to simple extraction: #{e.message}")
        results.map.with_index do |candidate, idx|
          {
            id: candidate.id,
            rank: idx + 1,
            score: 0.0,
            source: :elasticsearch
          }
        end
      end
    end
  end
end
