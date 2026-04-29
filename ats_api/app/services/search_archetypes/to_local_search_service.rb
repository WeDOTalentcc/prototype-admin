module SearchArchetypes
  class ToLocalSearchService
    def self.call(**args)
      new(**args).call
    end

    def initialize(archetype:, profile: "balanced", additional_options: {})
      @archetype = archetype
      @profile = profile
      @additional_options = additional_options
    end

    def call
      {
        search_text: build_search_text,
        where_filters: build_where_filters,
        filter_json: build_filter_json,
        order_json: build_order_json,
        max_pages: extract_max_pages,
        use_hybrid: should_use_hybrid?,
        limit: extract_limit
      }
    end

    private

    def build_search_text
      parts = []

      parts << @archetype.query if @archetype.query.present?
      parts << seniority_text if @archetype.seniority.present?
      parts << "#{@archetype.min_experience_years}+ anos de experiência" if @archetype.min_experience_years.present?
      parts << @archetype.location if @archetype.location.present?
      parts << @archetype.industry if @archetype.industry.present?
      parts << work_model_text if work_model_preference?
      parts << contract_type_text if contract_type_preference?

      merge_global_keywords(parts)

      parts.compact.join(" ").strip.presence || "*"
    end

    def build_where_filters
      filters = base_filters

      add_seniority_filter(filters)
      add_experience_filter(filters)
      add_location_filters(filters)
      add_work_model_filter(filters)
      add_contract_type_filter(filters)
      add_skills_filter(filters)
      add_languages_filter(filters)
      add_industry_filter(filters)
      merge_custom_where_filters(filters)

      filters.compact
    end

    def build_filter_json
      filters = {}

      add_global_filter_overrides(filters)

      filters.compact.to_json
    end

    def build_order_json
      order = @additional_options[:order] || default_order
      order.to_json
    end

    def default_order
      { updated_at: :desc }
    end

    def extract_max_pages
      @archetype.local_filters&.dig("max_pages")&.to_i ||
        @additional_options[:max_pages]&.to_i ||
        1
    end

    def extract_limit
      limit = @archetype.local_filters&.dig("limit") || @additional_options[:limit]
      (limit&.to_i || 50).clamp(1, 200)
    end

    def should_use_hybrid?
      return @additional_options[:use_hybrid] unless @additional_options[:use_hybrid].nil?

      @archetype.query.present? && @archetype.query.length > 10
    end

    def base_filters
      {
        is_deleted: false
      }
    end

    def add_seniority_filter(filters)
      return unless @archetype.seniority.present?

      levels = seniority_to_position_levels
      filters[:position_level] = { in: levels } if levels.any?
    end

    def add_experience_filter(filters)
      return unless @archetype.min_experience_years.present?

      filters[:years_of_experience_range] = { gte: @archetype.min_experience_years }
    end

    def add_location_filters(filters)
      return if @archetype.location.blank?

      city = extract_city
      state = extract_state

      filters[:city] = { ilike: "%#{city}%" } if city.present?
      filters[:state] = { ilike: "%#{state}%" } if state.present?
    end

    def add_work_model_filter(filters)
      return unless work_model_preference?

      case @archetype.work_model
      when "remote"
        filters[:remote_work] = true
      when "onsite"
        filters[:remote_work] = false
      when "hybrid"
        filters[:mobility] = { ilike: "%híbrido%" }
      end
    end

    def add_contract_type_filter(filters)
      return unless contract_type_preference?

      case @archetype.contract_type
      when "clt"
        filters[:clt_expectation] = { not: nil }
      when "pj"
        filters[:pj_expectation] = { not: nil }
      end
    end

    def add_skills_filter(filters)
      return if @archetype.skills.blank?

      filters[:skills] = { in: @archetype.skills.map(&:downcase) }
    end

    def add_languages_filter(filters)
      return if @archetype.languages.blank?

      filters[:languages] = { in: @archetype.languages.map(&:downcase) }
    end

    def add_industry_filter(filters)
      return if @archetype.industry.blank?

      filters[:current_company] = { ilike: "%#{@archetype.industry}%" }
    end

    def merge_custom_where_filters(filters)
      custom = @archetype.local_filters&.dig("where")
      return unless custom.is_a?(Hash)

      filters.merge!(custom.deep_symbolize_keys)
    end

    def add_global_filter_overrides(filters)
      global = @archetype.local_filters&.dig("filter")
      return unless global.is_a?(Hash)

      filters.merge!(global.deep_symbolize_keys)
    end

    def seniority_to_position_levels
      mapping = {
        "intern" => [ "Estágio", "Trainee" ],
        "junior" => [ "Júnior", "Junior" ],
        "mid" => [ "Pleno", "Mid-level" ],
        "senior" => [ "Sênior", "Senior" ],
        "lead" => [ "Tech Lead", "Lead", "Líder Técnico" ],
        "manager" => [ "Gerente", "Manager", "Coordenador" ],
        "director" => [ "Diretor", "Director" ],
        "c_level" => [ "VP", "CTO", "CEO", "CFO", "COO", "C-Level", "Executivo" ]
      }

      mapping[@archetype.seniority] || []
    end

    def seniority_text
      labels = {
        "intern" => "estágio",
        "junior" => "júnior",
        "mid" => "pleno",
        "senior" => "sênior",
        "lead" => "tech lead",
        "manager" => "gerente",
        "director" => "diretor",
        "c_level" => "executivo"
      }

      labels[@archetype.seniority]
    end

    def work_model_text
      labels = {
        "remote" => "remoto",
        "hybrid" => "híbrido",
        "onsite" => "presencial"
      }

      labels[@archetype.work_model]
    end

    def contract_type_text
      labels = {
        "clt" => "CLT",
        "pj" => "PJ",
        "freelance" => "freelancer"
      }

      labels[@archetype.contract_type]
    end

    def work_model_preference?
      @archetype.work_model.present? && @archetype.work_model != "any_work_model"
    end

    def contract_type_preference?
      @archetype.contract_type.present? && @archetype.contract_type != "any_contract"
    end

    def extract_city
      return nil if @archetype.location.blank?
      @archetype.location.split(",").first&.strip
    end

    def extract_state
      return nil if @archetype.location.blank?
      parts = @archetype.location.split(",")
      return nil if parts.size < 2
      parts[1]&.strip
    end

    def merge_global_keywords(parts)
      keywords = @archetype.local_filters&.dig("keywords")
      return unless keywords.present?

      keywords_array = keywords.is_a?(Array) ? keywords : [ keywords ]
      parts.concat(keywords_array)
    end
  end
end
