module SearchArchetypes
  class ToPearchParamsService
    SENIORITY_TO_TITLES = {
      "intern" => [ "Intern", "Estagiário", "Trainee" ],
      "junior" => [ "Junior", "Júnior", "Jr", "Associate" ],
      "mid" => [ "Mid-level", "Pleno", "Intermediate" ],
      "senior" => [ "Senior", "Sênior", "Sr" ],
      "lead" => [ "Lead", "Tech Lead", "Líder Técnico", "Team Lead" ],
      "manager" => [ "Manager", "Gerente", "Engineering Manager" ],
      "director" => [ "Director", "Diretor", "Head" ],
      "c_level" => [ "CTO", "CIO", "VP", "Chief", "C-Level" ]
    }.freeze

    WORK_MODEL_KEYWORDS = {
      "remote" => [ "remote", "remoto", "trabalho remoto", "home office" ],
      "hybrid" => [ "hybrid", "híbrido", "flexível" ],
      "onsite" => [ "onsite", "presencial", "on-site" ]
    }.freeze

    CONTRACT_TYPE_KEYWORDS = {
      "clt" => [ "CLT", "efetivo", "carteira assinada" ],
      "pj" => [ "PJ", "pessoa jurídica", "contractor" ],
      "freelance" => [ "freelance", "freelancer", "autônomo" ]
    }.freeze

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
        query: build_query,
        custom_filters: build_custom_filters,
        search_profile: @profile,
        limit: @additional_options[:limit] || default_limit,
        offset: @additional_options[:offset] || 0
      }.merge(build_optional_params)
    end

    private

    def build_query
      parts = []

      parts << @archetype.query if @archetype.query.present?
      parts << build_seniority_text if @archetype.seniority.present?
      parts << build_experience_text if @archetype.min_experience_years.present?
      parts << build_work_model_text if work_model_specified?
      parts << build_location_text if @archetype.location.present?
      parts << build_skills_text if @archetype.skills.present?
      parts << build_languages_text if @archetype.languages.present?
      parts << build_industry_text if @archetype.industry.present?

      merge_global_keywords(parts)

      parts.compact.join(" ").strip
    end

    def build_custom_filters
      filters = @archetype.global_filters&.deep_symbolize_keys || {}

      add_titles_filter(filters)
      add_locations_filter(filters)
      add_industries_filter(filters)
      add_languages_filter(filters)
      add_skills_filter(filters)
      add_experience_filter(filters)
      add_keywords_filter(filters)

      filters.compact
    end

    def build_optional_params
      params = {}

      params[:show_emails] = @additional_options[:show_emails] if @additional_options[:show_emails]
      params[:show_phone_numbers] = @additional_options[:show_phone_numbers] if @additional_options[:show_phone_numbers]
      params[:require_emails] = @additional_options[:require_emails] if @additional_options[:require_emails]
      params[:require_phone_numbers] = @additional_options[:require_phone_numbers] if @additional_options[:require_phone_numbers]
      params[:thread_id] = @additional_options[:thread_id] if @additional_options[:thread_id]
      params[:docid_blacklist] = @additional_options[:docid_blacklist] if @additional_options[:docid_blacklist]

      params
    end

    def add_titles_filter(filters)
      return if @archetype.query.blank? && @archetype.seniority.blank?

      titles = []

      titles << @archetype.query.split(/[,;]/).map(&:strip).first(3) if @archetype.query.present?

      if @archetype.seniority.present?
        seniority_titles = SENIORITY_TO_TITLES[@archetype.seniority] || []
        titles.concat(seniority_titles)
      end

      filters[:titles] = titles.flatten.uniq if titles.any?
    end

    def add_locations_filter(filters)
      return if @archetype.location.blank?

      filters[:locations] = [ @archetype.location ]
    end

    def add_industries_filter(filters)
      return if @archetype.industry.blank?

      filters[:industries] = [ @archetype.industry ]
    end

    def add_languages_filter(filters)
      return if @archetype.languages.blank?

      filters[:languages] = @archetype.languages
    end

    def add_skills_filter(filters)
      return if @archetype.skills.blank?

      filters[:keywords] = Array(filters[:keywords])
      filters[:keywords] += @archetype.skills
    end

    def add_experience_filter(filters)
      return if @archetype.min_experience_years.blank?

      filters[:min_total_experience_years] = @archetype.min_experience_years
    end

    def add_keywords_filter(filters)
      global_keywords = @archetype.global_filters&.dig("keywords")
      return if global_keywords.blank?

      filters[:keywords] = Array(filters[:keywords])
      keywords_array = global_keywords.is_a?(Array) ? global_keywords : [ global_keywords ]
      filters[:keywords] += keywords_array
    end

    def build_seniority_text
      return nil unless @archetype.seniority.present?

      label = @archetype.seniority_label
      "#{label} level"
    end

    def build_experience_text
      return nil unless @archetype.min_experience_years.present?

      years = @archetype.min_experience_years
      "with #{years}+ years of experience"
    end

    def build_work_model_text
      return nil unless work_model_specified?

      keywords = WORK_MODEL_KEYWORDS[@archetype.work_model]
      return nil unless keywords

      "preferring #{keywords.first} work"
    end

    def build_location_text
      return nil if @archetype.location.blank?

      "from #{@archetype.location}"
    end

    def build_skills_text
      return nil if @archetype.skills.blank?

      skills_list = @archetype.skills.first(5).join(", ")
      "with skills in #{skills_list}"
    end

    def build_languages_text
      return nil if @archetype.languages.blank?

      languages_list = @archetype.languages.join(" and ")
      "speaking #{languages_list}"
    end

    def build_industry_text
      return nil if @archetype.industry.blank?

      "in #{@archetype.industry} industry"
    end

    def merge_global_keywords(parts)
      global_keywords = @archetype.global_filters&.dig("keywords")
      return unless global_keywords.present?

      keywords = global_keywords.is_a?(Array) ? global_keywords.join(" ") : global_keywords
      parts << keywords if keywords.present?
    end

    def work_model_specified?
      @archetype.work_model.present? && @archetype.work_model != "any_work_model"
    end

    def default_limit
      case @profile.to_s
      when "fast" then 10
      when "balanced" then 10
      when "premium" then 10
      else 10
      end
    end
  end
end
