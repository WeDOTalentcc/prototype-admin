module Candidates
  class LocalSearchJob
    include Sidekiq::Job
    include Candidates::SearchProcessing

    POOL_SIZE = 150
    PAGE_SIZE = 10
    POOL_TTL = 30.minutes

    sidekiq_options queue: :sourcing_search, retry: 2

    def perform(account_id, user_id, sourcing_id, search_text, where_json, filter_json, order_json, max_pages = 1, return_sourced = false)
      @account = Account.find(account_id)
      @user = User.find(user_id)
      @return_sourced = return_sourced

      Current.user = @user
      Current.account = @account

      Apartment::Tenant.switch(@account.tenant) do
        execute_search(sourcing_id, search_text, where_json, filter_json)
      end
    rescue => e
      handle_error(account_id, sourcing_id, e)
    end

    private

    def execute_search(sourcing_id, search_text, where_json, filter_json)
      sourcing = Sourcing.find(sourcing_id)
      sourcing.update!(status: "processing")
      broadcast_sourcing_started(sourcing)

      user_filters = parse_json(where_json).merge(parse_json(filter_json))
      limit = sourcing.parameters["limit"]&.to_i || 10


      user_filters = apply_has_email_filter(user_filters, sourcing.parameters)
      user_filters = apply_has_phone_filter(user_filters, sourcing.parameters)
      user_filters = apply_has_email_or_phone_filter(user_filters, sourcing.parameters)
      user_filters = apply_years_of_experience_filter(user_filters)
      user_filters = apply_current_role_time_filter(user_filters)
      user_filters = apply_average_time_in_companies_filter(user_filters)
      user_filters = apply_hide_scope_filter(user_filters)
      user_filters = apply_current_job_titles_filter(user_filters, sourcing.parameters)
      user_filters = apply_previous_job_titles_filter(user_filters, sourcing.parameters)
      user_filters = apply_job_levels_filter(user_filters)
      user_filters = apply_function_area_list_filter(user_filters)

      if @return_sourced
        execute_sourced_profile_sourcings_search(sourcing, search_text, user_filters, limit)
      else
        execute_candidates_search(sourcing, search_text, user_filters, limit)
      end

      sourcing.update!(status: "done")
      broadcast_sourcing_completed(sourcing)
    end

    def execute_candidates_search(sourcing, search_text, user_filters, _limit)
      pool_size = POOL_SIZE
      page_size = Sourcings::FirstBatchPageSize.for_sourcing(sourcing)

      service = Search::HybridSearchService.new(
        account_id: @account.id,
        tenant: @account.tenant,
        sourcing_id: sourcing.id,
        user_id: @user.id
      )

      result = service.search(search_text, user_filters: user_filters, limit: pool_size, debug: true)

      sourcing.update!(
        search_metadata: result.metadata.to_json,
        search_explanation: result.explanation&.to_json
      )

      all_candidates = result.candidates
      search_meta_by_id = result.search_meta_by_id || {}
      all_candidate_ids = all_candidates.map(&:id)

      cache_search_pool(sourcing, all_candidate_ids, search_meta_by_id, page_size)

      first_batch = all_candidates.first(page_size)
      first_batch_meta = search_meta_by_id.slice(*first_batch.map(&:id))

      sourcing.update!(results_count: first_batch.size, local_results_count: first_batch.size)
      broadcast_sourcing_profiles_found(sourcing, first_batch.size, "local")

      processed = process_candidates_batch(first_batch, sourcing, @account, @user, search_meta_by_id: first_batch_meta)

      sourcing.update!(processed_count: processed)
      Rails.cache.write("sourcing_pool_page:#{sourcing.id}", 1, expires_in: POOL_TTL)
      broadcast_profiles_processing_completed(sourcing, processed)
    end

    def cache_search_pool(sourcing, candidate_ids, search_meta_by_id, page_size)
      Rails.cache.write(
        pool_cache_key(sourcing),
        {
          candidate_ids: candidate_ids,
          search_meta_by_id: search_meta_by_id,
          total: candidate_ids.size,
          page_size: page_size,
          created_at: Time.current.iso8601,
          expires_at: POOL_TTL.from_now.iso8601
        },
        expires_in: POOL_TTL
      )
    end

    def pool_cache_key(sourcing)
      "sourcing_pool:#{sourcing.id}:local"
    end

    def execute_sourced_profile_sourcings_search(sourcing, search_text, user_filters, limit)
      results = SourcedProfileSourcings::SearchService.call(
        query: search_text,
        account_id: @account.id,
        where: build_sourced_profile_sourcings_where(user_filters),
        limit: limit
      )

      process_sourced_profile_sourcings(results, sourcing)
    end

    def build_sourced_profile_sourcings_where(user_filters)
      where = {}
      where[:city] = user_filters[:city] if user_filters[:city].present?
      where[:state] = user_filters[:state] if user_filters[:state].present?
      where[:has_emails] = user_filters[:has_emails] if user_filters[:has_emails].present?
      where[:has_phone_numbers] = user_filters[:has_phone_numbers] if user_filters[:has_phone_numbers].present?
      where[:has_contact] = user_filters[:has_contact] if user_filters[:has_contact].present?

      if user_filters[:years_of_experience_min].present? || user_filters[:years_of_experience_max].present?
        range = {}
        range[:gte] = user_filters[:years_of_experience_min].to_i if user_filters[:years_of_experience_min].present?
        range[:lte] = user_filters[:years_of_experience_max].to_i if user_filters[:years_of_experience_max].present?
        where[:total_experience_years] = range
      end

      if user_filters[:current_role_time_min].present? || user_filters[:current_role_time_max].present?
        range = {}
        range[:gte] = user_filters[:current_role_time_min].to_i if user_filters[:current_role_time_min].present?
        range[:lte] = user_filters[:current_role_time_max].to_i if user_filters[:current_role_time_max].present?
        where[:current_role_time] = range
      end

      if user_filters[:average_time_in_companies_min].present? || user_filters[:average_time_in_companies_max].present?
        range = {}
        range[:gte] = user_filters[:average_time_in_companies_min].to_i if user_filters[:average_time_in_companies_min].present?
        range[:lte] = user_filters[:average_time_in_companies_max].to_i if user_filters[:average_time_in_companies_max].present?
        where[:average_time_in_companies] = range
      end

      # Filtro por position_level (mapeado de job_levels)
      where[:position_level] = user_filters[:position_level] if user_filters[:position_level].present?

      where[:sectors_a] = user_filters[:sectors_a] if user_filters[:sectors_a].present?

      where
    end

    def process_sourced_profile_sourcings(results, sourcing)
      total = results.total_count
      sourcing.update!(
        results_count: total,
        local_results_count: total
      )

      broadcast_sourcing_profiles_found(sourcing, total, "local_sourced")

      processed_count = 0
      failed_count = 0

      results.each_with_index do |sps_data, index|
        begin
          sourced_profile = SourcedProfile.find_by(id: sps_data[:sourced_profile_id])

          unless sourced_profile
            Rails.logger.error "❌ Profile #{sps_data[:sourced_profile_id]} não encontrado"
            failed_count += 1
            next
          end

          link_sourced_profile_to_sourcing(sourced_profile, sourcing)
          processed_count += 1
        rescue => e
          failed_count += 1
        end
      end

      sourcing.update!(
        processed_count: processed_count,
        results_count: processed_count
      )
    end

    def link_sourced_profile_to_sourcing(profile, sourcing)
      sps = SourcedProfileSourcing.find_or_create_by!(
        sourced_profile_id: profile.id,
        sourcing_id: sourcing.id,
        account_id: @account.id,
        user_id: @user.id
      ) do |new_sps|
        new_sps.is_deleted = false
        new_sps.search_source = "local_sourced"
      end

      sps
    end

    def apply_has_email_filter(user_filters, sourcing_params)
      has_email_param = sourcing_params["has_email"]
      has_email = ActiveModel::Type::Boolean.new.cast(has_email_param)
      return user_filters unless has_email == true
      user_filters.merge(has_emails: true)
    end

    def apply_has_phone_filter(user_filters, sourcing_params)
      has_phone_param = sourcing_params["has_phone"]
      has_phone = ActiveModel::Type::Boolean.new.cast(has_phone_param)
      return user_filters unless has_phone == true
      user_filters.merge(has_phone_numbers: true)
    end

    def apply_has_email_or_phone_filter(user_filters, sourcing_params)
      has_email_or_phone_param = sourcing_params["has_email_or_phone"]
      has_email_or_phone = ActiveModel::Type::Boolean.new.cast(has_email_or_phone_param)
      return user_filters unless has_email_or_phone == true
      user_filters.merge(has_contact: true)
    end

    def apply_years_of_experience_filter(user_filters)
      years_exp = user_filters[:years_of_experience]
      return user_filters unless years_exp.is_a?(Hash)

      result = user_filters.except(:years_of_experience)

      if years_exp[:gte].present? || years_exp["gte"].present?
        min_value = (years_exp[:gte] || years_exp["gte"]).to_i
        result[:years_of_experience_min] = min_value
      end

      if years_exp[:lte].present? || years_exp["lte"].present?
        max_value = (years_exp[:lte] || years_exp["lte"]).to_i
        result[:years_of_experience_max] = max_value
      end

      result
    end

    def apply_current_role_time_filter(user_filters)
      current_role_time = user_filters[:current_role_time] || user_filters["current_role_time"]

      return user_filters unless current_role_time.is_a?(Hash)

      result = user_filters.except(:current_role_time, "current_role_time")

      if current_role_time[:gte].present? || current_role_time["gte"].present?
        min_value = (current_role_time[:gte] || current_role_time["gte"]).to_i
        result[:current_role_time_min] = min_value
      end

      if current_role_time[:lte].present? || current_role_time["lte"].present?
        max_value = (current_role_time[:lte] || current_role_time["lte"]).to_i
        result[:current_role_time_max] = max_value
      end

      result
    end

    def apply_average_time_in_companies_filter(user_filters)
      avg_time = user_filters[:average_time_in_companies] || user_filters["average_time_in_companies"]

      return user_filters unless avg_time.is_a?(Hash)

      result = user_filters.except(:average_time_in_companies, "average_time_in_companies")

      if avg_time[:gte].present? || avg_time["gte"].present?
        min_value = (avg_time[:gte] || avg_time["gte"]).to_i
        result[:average_time_in_companies_min] = min_value
      end

      if avg_time[:lte].present? || avg_time["lte"].present?
        max_value = (avg_time[:lte] || avg_time["lte"]).to_i
        result[:average_time_in_companies_max] = max_value
      end

      result
    end

    def apply_current_job_titles_filter(user_filters, sourcing_params)
      current_job_titles = user_filters[:current_job_titles] || user_filters["current_job_titles"]
      scope = user_filters[:current_job_title_scope] || user_filters["current_job_title_scope"]

      if current_job_titles.blank?
        where_params = sourcing_params["where"] || sourcing_params[:where] || {}
        current_job_titles = where_params["current_job_titles"] || where_params[:current_job_titles]
        scope = where_params["current_job_title_scope"] || where_params[:current_job_title_scope]
      end

      if current_job_titles.present?
        user_filters[:current_job_titles] = current_job_titles
        user_filters[:current_job_title_scope] = scope || "current"
      end

      user_filters
    end

    def apply_previous_job_titles_filter(user_filters, sourcing_params)
      previous_job_titles = user_filters[:previous_job_titles] || user_filters["previous_job_titles"]

      if previous_job_titles.blank?
        where_params = sourcing_params["where"] || sourcing_params[:where] || {}
        previous_job_titles = where_params["previous_job_titles"] || where_params[:previous_job_titles]
      end

      if previous_job_titles.present?
        user_filters[:previous_experiences] = previous_job_titles
        user_filters.delete(:previous_job_titles)
        user_filters.delete("previous_job_titles")
      end

      user_filters
    end

    # Mapeia job_levels para position_level (campo indexado)
    def apply_job_levels_filter(user_filters)
      job_levels = user_filters[:job_levels] || user_filters["job_levels"]

      if job_levels.present?
        Rails.logger.info "[LocalSearchJob] 🎯 Mapping job_levels to position_level"
        Rails.logger.info "   job_levels: #{job_levels.inspect}"

        # Normalizar valores para lowercase (position_level é indexado em lowercase)
        normalized_levels = Array(job_levels).map { |level| level.to_s.strip.downcase }

        user_filters[:position_level] = normalized_levels
        user_filters.delete(:job_levels)
        user_filters.delete("job_levels")

        Rails.logger.info "   ✅ Mapped to position_level: #{user_filters[:position_level].inspect}"
      end

      user_filters
    end

    def apply_function_area_list_filter(user_filters)
      function_areas = user_filters[:function_area_list] || user_filters["function_area_list"]

      if function_areas.present?
        normalized_sectors = Array(function_areas).map { |area| area.to_s.strip.downcase }

        user_filters[:sectors_a] = normalized_sectors
        user_filters.delete(:function_area_list)
        user_filters.delete("function_area_list")
      end

      user_filters
    end

    def apply_hide_scope_filter(user_filters)
      hide_scope = user_filters[:hide_scope] || user_filters["hide_scope"]

      valid_scopes = [
        "viewed_by_me_this_project",
        "viewed_by_me_all_projects",
        "viewed_by_org_this_project",
        "viewed_by_org_all_projects"
      ]
      return user_filters unless valid_scopes.include?(hide_scope)

      period = (user_filters[:period] || user_filters["period"])&.to_i
      job_ids = extract_job_ids(user_filters)

      job_ids = [] if hide_scope.end_with?("all_projects")

      filter_by_user = hide_scope.start_with?("viewed_by_me_")
      user_id = filter_by_user ? @user.id : nil

      result = user_filters.except(:hide_scope, "hide_scope", :period, "period", :job_ids, "job_ids")

      if period.nil? || period <= 0
        return apply_no_period_filter(result, job_ids, hide_scope, user_id)
      end

      if job_ids.blank?
        return apply_period_only_filter(result, period, hide_scope, user_id)
      end

      apply_period_and_job_ids_filter(result, period, job_ids, hide_scope, user_id)
    end

    def extract_job_ids(user_filters)
      job_ids = user_filters[:job_ids] || user_filters["job_ids"]
      return [] if job_ids.blank?

      Array(job_ids).map(&:to_i).compact.uniq
    end

    def apply_no_period_filter(result, job_ids, hide_scope, user_id)
      if job_ids.blank?

        if user_id.present?
          excluded_candidate_ids = Apply
            .where(is_deleted: false)
            .where(user_id: user_id)
            .pluck(:candidate_id)
            .uniq

          if excluded_candidate_ids.any?
            result[:_not] = { id: excluded_candidate_ids }
          end
        else
          result[:has_valid_apply] = false
        end
      else
        if user_id.present?
          excluded_candidate_ids = Apply
            .where(is_deleted: false)
            .where(user_id: user_id)
            .where(job_id: job_ids)
            .pluck(:candidate_id)
            .uniq

          if excluded_candidate_ids.any?
            result[:_not] = { id: excluded_candidate_ids }
          end
        else
          result[:_not] = { all_apply_job_ids: job_ids }
        end
      end

      result
    end

    def apply_period_only_filter(result, period, hide_scope, user_id)
      if user_id.present?
        excluded_candidate_ids = Apply
          .where(is_deleted: false)
          .where(user_id: user_id)
          .where("applies.created_at >= ?", period.days.ago)
          .pluck(:candidate_id)
          .uniq

        if excluded_candidate_ids.any?
          result[:_not] = { id: excluded_candidate_ids }
        end
      else
        result[:last_valid_apply_days_ago] = { gt: period }
      end

      result
    end

    def apply_period_and_job_ids_filter(result, period, job_ids, hide_scope, user_id)
      query = Apply
        .where(is_deleted: false)
        .where(job_id: job_ids)
        .where("applies.created_at >= ?", period.days.ago)

      if user_id.present?
        query = query.where(user_id: user_id)
      end

      excluded_candidate_ids = query.pluck(:candidate_id).uniq

      if excluded_candidate_ids.any?
        result[:_not] = { id: excluded_candidate_ids }
      end

      result
    end

    def parse_json(json_string)
      return {} if json_string.blank?
      JSON.parse(json_string, symbolize_names: true)
    rescue JSON::ParserError
      {}
    end

    def merge_where_filters(base_where, parsed_where)
      result = base_where.deep_dup

      parsed_where.each do |field, value|
        result[field] = convert_filter_value(value)
      end

      result
    end

    FILTER_CONVERTERS = {
      ilike: ->(op, val) { val.to_s.gsub("%", "") },
      in: ->(op, val) { val },
      gte: ->(op, val) { { op => val } },
      gt: ->(op, val) { { op => val } },
      lte: ->(op, val) { { op => val } },
      lt: ->(op, val) { { op => val } },
      not_in: ->(op, val) { { not: val } }
    }.freeze

    VALUE_EXTRACTORS = {
      Array => ->(val) { val.map(&:to_s) },
      Hash => ->(val) { [ val.values.first.to_s.gsub("%", "") ] },
      String => ->(val) { [ val ] }
    }.freeze

    FILTER_SIMPLIFIERS = {
      Array => ->(val) { val.first },
      Hash => ->(val) { val.dig(:in, 0) if val[:in].is_a?(Array) }
    }.freeze

    AVAILABLE_SEARCH_FIELDS = [
      "name", "email", "role_name", "current_company", "city", "state",
      "country", "remote_work", "mobility", "skills", "languages",
      "education_levels", "position_level", "years_of_experience_range",
      "clt_expectation", "pj_expectation", "age_range", "curriculum_text"
    ].freeze

    def convert_filter_value(value)
      return value unless value.is_a?(Hash)

      operator = value.keys.first.to_sym
      operand = value.values.first

      converter = FILTER_CONVERTERS[operator]
      return value unless converter

      converter.call(operator, operand)
    end

    def fetch_page(search, where, filter, order, page, account_id)
      searchkick_where = build_searchkick_where(where, account_id)

      params = {
        where: searchkick_where,
        order: order.presence || { updated_at: :desc },
        page: page,
        per_page: 30
      }

      apply_filters!(params, filter) if filter.present?

      Rails.logger.info "[LocalSearchJob] Searchkick params: search_present=#{search.present?}, filter_keys=#{params[:where]&.keys}"

      results = Candidate.search(search, **params)

      Rails.logger.info "[LocalSearchJob] Found #{results.total_count} candidates"

      serialized_records = CandidateSerializer.new(results.results).serializable_hash[:data]

      {
        records: serialized_records,
        total_count: results.total_count
      }
    end

    def build_searchkick_where(where, account_id)
      base_where = { account_id: account_id, is_deleted: false }

      where.each_with_object(base_where) do |(field, value), hash|
        next if [ :account_id, :is_deleted ].include?(field.to_sym)
        hash[field] = value
      end
    end

    def process_search(sourcing, user, account, search, where, filter, order, max_pages)
      broadcast_profiles_processing_started(sourcing)

      candidates = search_candidates_hybrid(account, search, where)

      return process_candidates_fallback(sourcing, user, account, search, where, filter, order, max_pages) if candidates.empty?

      processed = process_candidates_batch(candidates, sourcing, account, user)
      broadcast_profiles_processing_completed(sourcing, processed)
    end

    def search_candidates_hybrid(account, search, where)
      service = Candidates::Search::HybridSearchService.new(
        account_id: account.id,
        tenant: account.tenant
      )

      service.search(search, filters: where, limit: 50)
    rescue => e
      Rails.logger.error "[LocalSearchJob] Hybrid search failed: #{e.message}"
      []
    end

    def process_candidates_fallback(sourcing, user, account, search, where, filter, order, max_pages)
      Rails.logger.info "[LocalSearchJob] Hybrid search returned 0, trying legacy fallback"

      page = 1
      total_processed = 0

      loop do
        results = fetch_page(search, where, filter, order, page, account.id)

        if results[:records].empty? && page == 1
          Rails.logger.info "[LocalSearchJob] No results found, trying fallback strategies"
          results = try_fallback_search(search, where, filter, order, account.id)
        end

        break if results[:records].empty?

        results[:records].each do |candidate_data|
          candidate = Candidate.find(candidate_data[:id])
          profile = create_or_update_sourced_profile(sourcing, candidate, account, user)
          Rails.logger.info "[LocalSearchJob] ⏳ Profile #{profile.id} will be analyzed by AI, broadcast will happen after analysis" if profile
          total_processed += 1
        end

        sourcing.update!(results_count: total_processed)

        break if page >= max_pages
        break unless has_more_pages?(page, results[:total_count])
        page += 1
      end
    end

    def try_fallback_search(original_search, where, filter, order, account_id)
      strategies = [
        {
          name: "text_in_search",
          search: build_search_from_filters(where),
          where: {},
          description: "Move all filter values to search query as free text (e.g., 'react node.js frontend')"
        },
        {
          name: "wildcard_search",
          search: "*",
          where: where,
          description: "Wildcard search (*) keeping structured filters (good for very specific filters)"
        },
        # {
        #   name: "partial_filters",
        #   search: original_search,
        #   where: simplify_filters(where),
        #   description: "Simplify complex filters - use only first value from arrays (less restrictive)"
        # },
        {
          name: "only_search",
          search: "#{original_search} #{extract_keywords(where)}".strip,
          where: {},
          description: "Concatenate original search + all filter keywords as plain text search"
        }
      ]

      strategies.each do |strategy|
        Rails.logger.info "[LocalSearchJob] 🔄 Trying fallback: #{strategy[:description]}"
        Rails.logger.info "[LocalSearchJob]    strategy filter_keys=#{strategy[:where]&.keys}"

        results = fetch_page(strategy[:search], strategy[:where], filter, order, 1, account_id)

        if results[:total_count] > 0
          Rails.logger.info "[LocalSearchJob] ✅ Fallback '#{strategy[:name]}' found #{results[:total_count]} results"
          return results
        else
          Rails.logger.info "[LocalSearchJob] ❌ Strategy '#{strategy[:name]}' returned 0 results"
        end
      end

      Rails.logger.info "[LocalSearchJob] 🤖 All strategies failed, consulting LLM for alternative approach"
      llm_suggestion = ask_llm_for_alternative(original_search, where)

      if llm_suggestion
        Rails.logger.info "[LocalSearchJob] 💡 LLM suggested alternative: filter_keys=#{llm_suggestion[:where]&.keys}"
        results = fetch_page(llm_suggestion[:search], llm_suggestion[:where], filter, order, 1, account_id)

        if results[:total_count] > 0
          Rails.logger.info "[LocalSearchJob] ✅ LLM suggestion found #{results[:total_count]} results!"
          return results
        end
      end

      Rails.logger.info "[LocalSearchJob] ❌ All fallback strategies including LLM failed"
      { records: [], total_count: 0 }
    end

    def ask_llm_for_alternative(original_search, original_where)
      prompt = build_llm_prompt(original_search, original_where)
      response = call_gemini_api(prompt)

      return nil unless response

      parse_llm_response(response)
    rescue => e
      Rails.logger.error "[LocalSearchJob] ❌ LLM fallback failed: #{e.message}"
      nil
    end

    def build_llm_prompt(search, filters)
      <<~PROMPT
        A busca de candidatos retornou 0 resultados. Preciso de uma estratégia alternativa.

        **Busca Original:**
        - Search term: "#{search}"
        - Filters: #{filters.inspect}

        **Problema:** No results found with current search strategy

        **Campos disponíveis no Elasticsearch:**
        #{AVAILABLE_SEARCH_FIELDS.join(', ')}

        **Sua tarefa:**
        Sugira uma busca alternativa mais ampla que ainda seja relevante. Considere:
        1. Remover filtros muito específicos
        2. Usar termos mais genéricos
        3. Focar nos conceitos principais
        4. Considerar sinônimos ou termos relacionados

        Retorne APENAS JSON válido (sem markdown):
        {
          "search": "termo de busca mais amplo",
          "where": { "campo": "valor simplificado" },
          "reasoning": "explicação da mudança"
        }
      PROMPT
    end

    def call_gemini_api(prompt)
      Llm::Gateway.chat(
        messages: [
          { role: "system", content: "Você é um especialista em otimização de buscas em banco de dados." },
          { role: "user", content: prompt }
        ],
        temperature: 0.3,
        max_tokens: 800,
        response_format: { type: "json_object" },
        tracking: { operation: "local_search.query_optimization" }
      )
    end

    def parse_llm_response(response)
      content = response.dig("choices", 0, "message", "content")
      return nil unless content

      clean_content = clean_json_response(content)
      data = JSON.parse(clean_content, symbolize_names: true)

      Rails.logger.info "[LocalSearchJob] 🧠 LLM reasoning: #{data[:reasoning]}"

      {
        search: data[:search] || "*",
        where: data[:where] || {}
      }
    end

    def clean_json_response(content)
      content.strip
             .gsub(/^```json\s*\n?/, "")
             .gsub(/^```\s*\n?/, "")
             .gsub(/\n?```$/, "")
             .strip
    end

    def build_search_from_filters(where)
      terms = where.reject { |field, _| [ :account_id, :is_deleted ].include?(field.to_sym) }
                   .flat_map { |_, value| extract_value_terms(value) }
                   .compact

      terms.join(" ").presence || "*"
    end

    def extract_value_terms(value)
      extractor = VALUE_EXTRACTORS[value.class] || VALUE_EXTRACTORS[String]
      extractor.call(value)
    end

    def simplify_filters(where)
      where.reject { |field, _| [ :account_id, :is_deleted ].include?(field.to_sym) }
           .transform_values { |value| simplify_filter_value(value) }
           .compact
    end

    def simplify_filter_value(value)
      simplifier = FILTER_SIMPLIFIERS[value.class]
      return simplifier.call(value) if simplifier
      value
    end

    def extract_keywords(where)
      where.values
           .flat_map { |value| extract_value_terms(value) }
           .compact
           .join(" ")
    end

    def apply_filters!(params, filter)
      filter.each do |field, value|
        next unless value.present?

        apply_array_filter(params, field, value) and next if value.is_a?(Array)
        params[:where][field.to_s] = value
      end
    end

    def apply_array_filter(params, field, values)
      params[:where][:_or] ||= []
      or_conditions = values.map { |val| { field.to_s => { like: "%#{val.to_s.downcase}%" } } }
      params[:where][:_or].concat(or_conditions)
    end

    def has_more_pages?(current_page, total_count)
      return false if total_count.nil? || total_count.zero?
      current_page < (total_count.to_f / 30).ceil
    end

    def broadcast_sourcing_started(sourcing)
      serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_started",
          sourcing: serialized
        }
      )
    end

    def broadcast_sourcing_completed(sourcing)
      serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_completed",
          sourcing: serialized,
          success: true,
          error: nil
        }
      )
    end

    def handle_error(account_id, sourcing_id, exception)
      Rails.logger.error("[LocalSearchJob] Failed: #{exception.message}")
      Rails.logger.error(exception.backtrace.join("\n"))

      Apartment::Tenant.switch(Account.find(account_id).tenant) do
        sourcing = Sourcing.find_by(id: sourcing_id)
        return unless sourcing

        sourcing.update(status: "failed")
        serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

        SourcingChannel.broadcast_to(
          "#{sourcing.user_id}_sourcing_#{sourcing.id}",
          {
            type: "sourcing_failed",
            sourcing: serialized,
            error: exception.message
          }
        )
      end
    end
  end
end
