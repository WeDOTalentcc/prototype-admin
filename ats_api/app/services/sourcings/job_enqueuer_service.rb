module Sourcings
  class JobEnqueuerService
    def initialize(user:, sourcing:, query:, params:)
      @user = user
      @account = user.account
      @sourcing = sourcing
      @query = query
      @params = params
    end

    def call
      source = @params[:source]


      raise ArgumentError, "Invalid source: #{source}. Expected 'local', 'global', or 'linkedin'" unless %w[local global linkedin].include?(source)

      return enqueue_local_search if source == "local"
      return enqueue_linkedin_search if source == "linkedin"

      Rails.logger.info "[JobEnqueuerService] Enqueuing GLOBAL search for sourcing #{@sourcing.id}"
      enqueue_global_search
    end

    private

    # Enfileira busca LOCAL híbrida (Elasticsearch + Embeddings)
    # Ver documentação completa no cabeçalho deste arquivo
    def enqueue_local_search
      max_pages = @params[:max_pages]&.to_i || 1
      return_sourced = @params[:return_sourced] || false

      where_params = @params[:where] || {}

      Candidates::LocalSearchJob.perform_async(
        @account.id,
        @user.id,
        @sourcing.id,
        @query,
        where_params.to_json,
        (@params[:filter] || {}).to_json,
        (@params[:order] || {}).to_json,
        max_pages,
        return_sourced
      )
    end

    def enqueue_global_search
      params = filtered_params
      params = apply_years_of_experience_to_custom_filters(params)
      params = apply_pearch_filters_to_custom_filters(params)
      params = apply_default_pearch_limit(params)

      Pearch::TalentSearchJob.perform_async(
        @account.id,
        @user.id,
        @sourcing.id,
        @query,
        params.to_json
      )

      Rails.logger.info "[JobEnqueuerService] ✅ Pearch::TalentSearchJob enqueued successfully"
    end

    def enqueue_linkedin_search
      linkedin_params = build_linkedin_params

      Apify::LinkedinSearchJob.perform_async(
        @account.id,
        @user.id,
        @sourcing.id,
        linkedin_params.to_json
      )

      Rails.logger.info "[JobEnqueuerService] ✅ Apify::LinkedinSearchJob enqueued successfully"
    end

    def filtered_params
      @params.except(:controller, :action, :query, :async, :sourcing_id)
    end

    def apply_default_pearch_limit(params)
      params[:limit] = Sourcings::FirstBatchPageSize.for_sourcing(@sourcing)
      params.delete("limit") if params.key?("limit")
      params
    end

    def apply_years_of_experience_to_custom_filters(params)
      where = params[:where] || {}
      years_exp = where[:years_of_experience] || where["years_of_experience"]

      return params unless years_exp.is_a?(Hash)

      new_where = where.except(:years_of_experience, "years_of_experience")
      params[:where] = new_where if new_where.any?
      params.delete(:where) if new_where.empty?

      custom_filters = params[:custom_filters] || params["custom_filters"] || {}
      custom_filters = custom_filters.deep_dup if custom_filters.is_a?(Hash)

      years_filter = {}
      years_filter[:min] = (years_exp[:gte] || years_exp["gte"]).to_i if years_exp[:gte].present? || years_exp["gte"].present?
      years_filter[:max] = (years_exp[:lte] || years_exp["lte"]).to_i if years_exp[:lte].present? || years_exp["lte"].present?

      custom_filters[:years_experience] = years_filter if years_filter.any?
      params[:custom_filters] = custom_filters

      params
    end

    def apply_pearch_filters_to_custom_filters(params)
      where = params[:where] || {}
      return params if where.empty?

      custom_filters = params[:custom_filters] || {}
      custom_filters = custom_filters.deep_dup if custom_filters.is_a?(Hash)

      if where[:min_current_experience_years].present? || where["min_current_experience_years"].present?
        years = (where[:min_current_experience_years] || where["min_current_experience_years"]).to_f
        months = (years * 12).to_i
        custom_filters[:min_current_experience_months] = months
        where = where.except(:min_current_experience_years, "min_current_experience_years")
      end

      if where[:max_current_experience_years].present? || where["max_current_experience_years"].present?
        years = (where[:max_current_experience_years] || where["max_current_experience_years"]).to_f
        months = (years * 12).to_i
        custom_filters[:max_current_experience_months] = months
        where = where.except(:max_current_experience_years, "max_current_experience_years")
      end

      if where[:current_job_titles].present? || where["current_job_titles"].present?
        titles = where[:current_job_titles] || where["current_job_titles"]
        scope = where[:current_job_title_scope] || where["current_job_title_scope"] || "current_and_history"

        custom_filters[:titles] = Array(titles).map(&:to_s)

        where = where.except(:current_job_titles, "current_job_titles",
                            :current_job_title_scope, "current_job_title_scope")
      end

      if where[:previous_job_titles].present? || where["previous_job_titles"].present?
        prev_titles = where[:previous_job_titles] || where["previous_job_titles"]

        existing_titles = custom_filters[:titles] || []
        custom_filters[:titles] = (existing_titles + Array(prev_titles).map(&:to_s)).uniq

        where = where.except(:previous_job_titles, "previous_job_titles")
      end

      if where[:job_levels].present? || where["job_levels"].present?
        job_levels = Array(where[:job_levels] || where["job_levels"]).map(&:to_s)

        level_keywords = job_levels.flat_map do |level|
          normalized = level.downcase.strip

          case normalized
          when "estagiário", "intern"
            [ "intern", "estagiário", "internship", "estagio" ]
          when "trainee"
            [ "trainee", "programa trainee", "trainee program" ]
          when "junior", "júnior"
            [ "junior", "júnior", "jr", "entry level", "jr.", "junior level" ]
          when "pleno", "mid", "mid-level", "mid level", "midlevel"
            [ "pleno", "mid-level", "midlevel", "intermediate", "mid level", "middle" ]
          when "senior", "sênior"
            [ "senior", "sênior", "sr", "sr.", "lead", "senior level" ]
          when "especialista", "specialist", "expert"
            [ "specialist", "especialista", "expert", "principal", "staff" ]
          when "coordenador", "coordinator"
            [ "coordinator", "coordenador", "tech lead", "team lead", "lead" ]
          when "gerente", "manager"
            [ "manager", "gerente", "engineering manager", "head", "gestor" ]
          when "diretor", "director"
            [ "director", "diretor", "head of", "vp", "vice president" ]
          when "vice_president", "vice-president", "vice president"
            [ "vice president", "VP", "vice-president", "vice-presidente" ]
          when "c_level", "c-level", "c level", "executive"
            [ "CTO", "CEO", "CPO", "CMO", "CFO", "COO", "C-level", "executive", "chief", "C-Level" ]
          when "sócio", "partner"
            [ "partner", "sócio", "socio", "founding partner", "sócio-fundador" ]
          when "proprietário", "owner"
            [ "owner", "proprietário", "proprietario", "founder", "fundador", "co-founder" ]
          else
            [ normalized ]
          end
        end.uniq

        custom_filters[:keywords] ||= []
        custom_filters[:keywords] = (custom_filters[:keywords] + level_keywords).uniq

        where = where.except(:job_levels, "job_levels")
      end

      # Mapeia function_area_list para keywords (busca nos perfis)
      # Usa os nomes dos setores diretamente sem mapeamento hardcoded
      if where[:function_area_list].present? || where["function_area_list"].present?
        function_areas = Array(where[:function_area_list] || where["function_area_list"])
          .map { |area| area.to_s.strip.downcase }
          .reject(&:blank?)

        custom_filters[:keywords] ||= []
        custom_filters[:keywords] = (custom_filters[:keywords] + function_areas).uniq

        where = where.except(:function_area_list, "function_area_list")
      end

      if where[:top_universities].present? || where["top_universities"].present?
        custom_filters[:studied_at_top_universities] = true
        where = where.except(:top_universities, "top_universities")
      end

      if where[:startup_experience].present? || where["startup_experience"].present?
        custom_filters[:has_startup_experience] = true
        where = where.except(:startup_experience, "startup_experience")
      end

      if where[:decision_maker].present? || where["decision_maker"].present?
        is_decision_maker = ActiveModel::Type::Boolean.new.cast(
          where[:decision_maker] || where["decision_maker"]
        )

        if is_decision_maker
          custom_filters[:titles] ||= []
          custom_filters[:titles] += [ "CEO", "Founder", "Co-Founder", "CTO", "Head", "Director", "VP" ]
          custom_filters[:titles].uniq!
        end

        where = where.except(:decision_maker, "decision_maker")
      end

      if where[:open_to_opportunities].present? || where["open_to_opportunities"].present?
        is_open = ActiveModel::Type::Boolean.new.cast(
          where[:open_to_opportunities] || where["open_to_opportunities"]
        )

        if is_open
          custom_filters[:keywords] ||= []
          custom_filters[:keywords] += [ "open to work", "open to opportunities", "seeking opportunities" ]
          custom_filters[:keywords].uniq!
        end

        where = where.except(:open_to_opportunities, "open_to_opportunities")
      end

      params[:where] = where if where.any?
      params.delete(:where) if where.empty?

      params[:custom_filters] = custom_filters if custom_filters.any?
      params
    end

    def build_linkedin_params
      where = @params[:where] || {}
      {
        query: @query,
        current_job_titles: where[:current_job_titles] || where["current_job_titles"],
        past_job_titles: where[:previous_job_titles] || where["previous_job_titles"],
        locations: extract_linkedin_locations(where),
        current_companies: where[:current_companies] || where["current_companies"],
        past_companies: where[:past_companies] || where["past_companies"],
        schools: where[:schools] || where["schools"],
        industries: where[:industries] || where["industries"],
        years_of_experience: extract_linkedin_experience(where),
        mode: @params[:linkedin_mode] || "full_with_email",
        take_pages: @params[:take_pages],
        max_items: @params[:max_items],
        seniority_levels: where[:seniority_levels] || where["seniority_levels"],
        functions: where[:functions] || where["functions"],
        company_headcount: where[:company_headcount] || where["company_headcount"],
        profile_languages: where[:profile_languages] || where["profile_languages"],
        first_names: where[:first_names] || where["first_names"],
        last_names: where[:last_names] || where["last_names"],
        recently_changed_jobs: where[:recently_changed_jobs] || where["recently_changed_jobs"],
        company_headquarter_locations: where[:company_headquarter_locations] || where["company_headquarter_locations"],
        exclude_locations: where[:exclude_locations] || where["exclude_locations"],
        exclude_current_companies: where[:exclude_current_companies] || where["exclude_current_companies"],
        exclude_past_companies: where[:exclude_past_companies] || where["exclude_past_companies"],
        exclude_schools: where[:exclude_schools] || where["exclude_schools"],
        exclude_current_job_titles: where[:exclude_current_job_titles] || where["exclude_current_job_titles"],
        exclude_past_job_titles: where[:exclude_past_job_titles] || where["exclude_past_job_titles"],
        exclude_industry_ids: where[:exclude_industry_ids] || where["exclude_industry_ids"],
        exclude_seniority_levels: where[:exclude_seniority_levels] || where["exclude_seniority_levels"],
        exclude_function_ids: where[:exclude_function_ids] || where["exclude_function_ids"],
        exclude_company_headquarter_locations: where[:exclude_company_headquarter_locations] || where["exclude_company_headquarter_locations"]
      }.compact
    end

    def extract_linkedin_locations(where)
      locations = where[:locations] || where["locations"]
      return Array(locations) if locations.present?

      city = where[:city] || where["city"]
      state = where[:state] || where["state"]
      return ["#{city}, #{state}".strip.delete_suffix(",")] if city.present? || state.present?

      nil
    end

    def extract_linkedin_experience(where)
      years_exp = where[:years_of_experience] || where["years_of_experience"]
      return nil unless years_exp.is_a?(Hash)

      min = years_exp[:gte] || years_exp["gte"]
      max = years_exp[:lte] || years_exp["lte"]
      return nil unless min || max

      ["#{min || 0}-#{max || 30}"]
    end
  end
end
