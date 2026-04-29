# frozen_string_literal: true

module Candidates
  class LoadMoreCandidatesJob
    include Sidekiq::Job
    include Candidates::SearchProcessing

    POOL_CACHE_PREFIX = "sourcing_pool"

    sidekiq_options queue: :sourcing_search, retry: 2

    def perform(account_id, user_id, sourcing_id, page, page_size = Sourcings::FirstBatchPageSize::BASE)
      @account = Account.find(account_id)
      @user = User.find(user_id)

      Apartment::Tenant.switch(@account.tenant) do
        execute_load_more(sourcing_id, page, page_size)
      end
    rescue => e
      handle_error(account_id, user_id, sourcing_id, e)
    end

    private

    def execute_load_more(sourcing_id, page, page_size)
      sourcing = Sourcing.find(sourcing_id)

      local_cache = Rails.cache.read("#{POOL_CACHE_PREFIX}:#{sourcing_id}:local")
      global_cache = Rails.cache.read("#{POOL_CACHE_PREFIX}:#{sourcing_id}:global")
      has_global_source = sourcing.parameters&.dig("sources")&.include?("global")
      has_local_source = sourcing.parameters&.dig("sources")&.include?("local")

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [LoadMoreCandidatesJob] Processing page #{page}"
      Rails.logger.info "   Sourcing: #{sourcing_id} | Page Size: #{page_size}"
      Rails.logger.info "   Local cache: #{local_cache.present?} (#{local_cache&.dig(:total) || 0} total)"
      Rails.logger.info "   Global cache: #{global_cache.present?} (#{global_cache&.dig(:total) || 0} total)"
      Rails.logger.info "   Sources: local=#{has_local_source} | global=#{has_global_source}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      broadcast_load_more_started(sourcing, page, page_size)

      unless has_local_source || has_global_source
        broadcast_pool_expired(sourcing)
        return
      end

      processed_total = 0

      if has_local_source
        processed_local = 0
        processed_local = process_local_page(sourcing, local_cache, page, page_size) if local_cache.present?

        if processed_local.zero?
          Rails.logger.info "   📦 Local cache empty/exhausted for page #{page}, searching for more candidates"
          processed_local = fetch_local_page_with_search(sourcing, page, page_size)
        end

        processed_total += processed_local
        Rails.logger.info "   📦 Local processed: #{processed_local}"
      end

      if has_global_source
        processed_global = 0
        processed_global = process_global_page(sourcing, global_cache, page, page_size) if global_cache.present?

        if processed_global.zero?
          Rails.logger.info "   🌍 Global cache empty/exhausted for page #{page}, fetching from Pearch with offset"
          processed_global = fetch_global_page_with_offset(sourcing, page, page_size)
        end

        processed_total += processed_global
        Rails.logger.info "   🌍 Global processed: #{processed_global}"
      end

      if processed_total.zero?
        Rails.logger.info "   ⚠️ No new candidates processed on page #{page}"
        broadcast_pool_expired(sourcing)
        return
      end

      active_sourcings = sourcing.sourced_profile_sourcings.active

      total_count = active_sourcings.count

      local_count = active_sourcings
        .joins(:sourced_profile)
        .where(sourced_profiles: { provider: %w[local hybrid] })
        .count

      global_count = active_sourcings
        .joins(:sourced_profile)
        .where(sourced_profiles: { provider: %w[pearch linkedin] })
        .count

      sourcing.update!(
        processed_count: total_count,
        results_count: total_count,
        local_results_count: local_count,
        global_results_count: global_count
      )

      Rails.cache.delete("load_more_lock:#{sourcing.id}:#{page}")

      total_pages = calculate_total_pages(local_cache, global_cache, page_size)
      total_items = calculate_total_items(local_cache, global_cache)

      Rails.logger.info "   ✅ Total processed: #{processed_total} | Page: #{page}/#{total_pages} | Total candidates: #{total_count}"

      broadcast_load_more_completed(sourcing, processed_total, page, total_pages, total_items)
    end

    def process_local_page(sourcing, cache_data, page, page_size)
      candidate_ids = cache_data[:candidate_ids]
      search_meta_by_id = cache_data[:search_meta_by_id] || {}

      start_index = (page - 1) * page_size
      page_ids = candidate_ids.slice(start_index, page_size)

      return 0 if page_ids.blank?

      broadcast_processing_source(sourcing, "local", page_ids.size)

      candidates = load_candidates_in_order(page_ids)
      page_meta = search_meta_by_id.slice(*page_ids)

      process_candidates_batch(candidates, sourcing, @account, @user, search_meta_by_id: page_meta)
    end

    def process_global_page(sourcing, cache_data, page, page_size)
      search_results = cache_data[:search_results]

      start_index = (page - 1) * page_size
      page_results = search_results.slice(start_index, page_size)

      return 0 if page_results.blank?

      broadcast_processing_source(sourcing, "global", page_results.size)

      processed_count = 0
      page_results.each_with_index do |result, index|
        profile = create_sourced_profile_from_pearch(sourcing, result, @account)
        if profile
          processed_count += 1
          broadcast_load_more_profile_processed(sourcing, profile.id, processed_count, page_results.size, "global")
        end
      rescue => e
        Rails.logger.error "[LoadMoreCandidatesJob] Failed to process global profile: #{e.message}"
      end

      processed_count
    end

    def fetch_global_page_with_offset(sourcing, page, page_size)
      offset = (page - 1) * page_size

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🌍 [LoadMoreCandidatesJob] Fetching global page via Pearch offset"
      Rails.logger.info "   Page: #{page} | Offset: #{offset} | Limit: #{page_size}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      pearch_params = {
        limit: page_size,
        offset: offset,
        source: "global"
      }
      pearch_params[:thread_id] = sourcing.thread_id if sourcing.thread_id.present?

      service = Pearch::TalentSearchExecutorService.new(
        user: @user,
        query: sourcing.query,
        params: pearch_params
      )

      result = service.call
      return 0 unless result[:success]

      search_results = result.dig(:data, :search_results) || []
      return 0 if search_results.empty?

      processed_count = 0
      search_results.each do |sr|
        result_data = sr.is_a?(Hash) ? sr.deep_symbolize_keys : sr
        profile = create_sourced_profile_from_pearch(sourcing, result_data, @account)
        next unless profile

        processed_count += 1
        broadcast_load_more_profile_processed(sourcing, profile.id, processed_count, search_results.size, "global")
      rescue => e
        Rails.logger.error "[LoadMoreCandidatesJob] Offset global profile failed: #{e.message}"
      end

      Rails.logger.info "🌍 [LoadMoreCandidatesJob] Offset fetch processed #{processed_count} profiles"
      processed_count
    rescue => e
      Rails.logger.error "[LoadMoreCandidatesJob] Pearch offset fetch failed: #{e.message}"
      0
    end

    def fetch_local_page_with_search(sourcing, page, page_size)
      processed_candidate_ids = sourcing.sourced_profiles
        .where.not(candidate_id: nil)
        .pluck(:candidate_id)

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "📦 [LoadMoreCandidatesJob] Fetching local page via Searchkick fallback"
      Rails.logger.info "   Page: #{page} | Limit: #{page_size} | Excluding: #{processed_candidate_ids.size} already processed"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      where_conditions = { account_id: @account.id, is_deleted: false }
      where_conditions[:id] = { not: processed_candidate_ids } if processed_candidate_ids.any?

      sourcing_where = sourcing.parameters&.dig("where") || {}
      where_conditions[:city] = sourcing_where["city"] if sourcing_where["city"].present?
      where_conditions[:state] = sourcing_where["state"] if sourcing_where["state"].present?
      where_conditions[:has_emails] = true if sourcing_where["has_emails"].present?
      where_conditions[:has_phone_numbers] = true if sourcing_where["has_phone_numbers"].present?

      results = Candidate.search(
        sourcing.query.presence || "*",
        where: where_conditions,
        limit: page_size,
        order: { _score: :desc }
      )

      candidates = results.to_a
      return 0 if candidates.empty?

      Rails.logger.info "   📦 Local search fallback found #{candidates.size} new candidates"
      process_candidates_batch(candidates, sourcing, @account, @user, search_meta_by_id: {})
    rescue => e
      Rails.logger.error "[LoadMoreCandidatesJob] Local search fallback failed: #{e.message}"
      0
    end

    def create_sourced_profile_from_pearch(sourcing, result, account)
      profile_data = result[:profile] || {}
      all_emails = extract_all_emails(profile_data)
      primary_email = all_emails.first
      all_phones = extract_all_phones(profile_data)
      primary_phone = all_phones.first
      cpf = profile_data[:cpf]
      linkedin_url = profile_data[:linkedin_url]

      matcher = SourcedProfiles::ProfileMatchingService.new(account_id: account.id)
      existing_profile = matcher.find_duplicate(
        email: primary_email,
        phone: primary_phone,
        cpf: cpf,
        linkedin_url: linkedin_url,
        external_id: result[:docid]
      )

      if existing_profile
        merge_profile_data(existing_profile, profile_data, primary_email, all_emails, primary_phone, all_phones, result)
        create_or_update_sourced_profile_sourcing(existing_profile, sourcing, result)
        return existing_profile
      end

      profile = create_new_profile(account, result, profile_data, primary_email, all_emails, primary_phone, all_phones)
      create_or_update_sourced_profile_sourcing(profile, sourcing, result)
      profile
    end

    def calculate_total_pages(local_cache, global_cache, page_size)
      local_total = local_cache&.dig(:total) || 0
      global_total = global_cache&.dig(:total) || 0
      max_total = [ local_total, global_total ].max
      (max_total.to_f / page_size).ceil
    end

    def calculate_total_items(local_cache, global_cache)
      (local_cache&.dig(:total) || 0) + (global_cache&.dig(:total) || 0)
    end

    def extract_all_emails(profile_data)
      business_emails = Array(profile_data[:business_emails]).compact
      personal_emails = Array(profile_data[:personal_emails]).compact
      all_emails = business_emails + personal_emails
      all_emails.uniq.reject(&:blank?)
    end

    def extract_all_phones(profile_data)
      phone_numbers = Array(profile_data[:phone_numbers]).compact
      phone_numbers.uniq.reject(&:blank?)
    end

    def merge_profile_data(profile, profile_data, primary_email, all_emails, primary_phone, all_phones, result)
      curriculum_text = build_curriculum_text(profile_data, result)
      current_company = extract_current_company(profile_data)
      current_title = extract_current_title(profile_data)

      updates = {
        email: primary_email.presence || profile.email,
        emails: all_emails.any? ? all_emails : profile.emails,
        phone: primary_phone.presence || profile.phone,
        phones: all_phones.any? ? all_phones : profile.phones,
        picture_url: profile_data[:picture_url].presence || profile.picture_url,
        summary: profile_data[:summary].presence || profile.summary,
        curriculum_text: curriculum_text.presence || profile.curriculum_text,
        title: profile_data[:title].presence || profile.title,
        location: profile_data[:location].presence || profile.location,
        city: profile_data[:city].presence || profile.city,
        state: profile_data[:state].presence || profile.state,
        country: profile_data[:country].presence || profile.country,
        cpf: profile_data[:cpf].presence || profile.cpf,
        date_birth: parse_date(profile_data[:date_birth]) || profile.date_birth,
        linkedin_url: profile_data[:linkedin_url].presence || profile.linkedin_url,
        linkedin_slug: profile_data[:linkedin_slug].presence || profile.linkedin_slug,
        first_name: profile_data[:first_name].presence || profile.first_name,
        last_name: profile_data[:last_name].presence || profile.last_name,
        estimated_age: profile_data[:estimated_age] || profile.estimated_age,
        total_experience_years: profile_data[:total_experience_years] || profile.total_experience_years,
        is_decision_maker: profile_data[:is_decision_maker] || profile.is_decision_maker,
        is_top_universities: profile_data[:is_top_universities] || profile.is_top_universities,
        followers_count: profile_data[:followers_count] || profile.followers_count,
        connections_count: profile_data[:connections_count] || profile.connections_count,
        has_emails: (primary_email.presence || profile.email).present?,
        has_phone_numbers: (primary_phone.presence || profile.phone).present?,
        current_company: current_company.presence || profile.current_company,
        current_title: current_title.presence || profile.current_title,
        role_name: profile_data[:role_name].presence || profile_data[:title].presence || current_title.presence || profile.role_name,
        position_level: profile_data[:position_level].presence || profile.position_level,
        remote_work: profile_data[:remote_work].presence || profile.remote_work,
        mobility: profile_data[:mobility].nil? ? profile.mobility : profile_data[:mobility],
        profile_updated_at: Time.current
      }

      updates[:expertise] = merge_arrays(profile.expertise, profile_data[:expertise])
      updates[:languages_data] = profile_data[:languages].presence || profile.languages_data
      updates[:skills_data] = merge_arrays(profile.skills_data, profile_data[:skills])
      updates[:experiences_data] = profile_data[:experiences].presence || profile.experiences_data
      updates[:educations_data] = profile_data[:educations].presence || profile.educations_data
      updates[:certifications_data] = profile_data[:certifications].presence || profile.certifications_data
      updates[:awards_data] = profile_data[:awards].presence || profile.awards_data

      if profile.provider == "local" && profile_data.present?
        updates[:provider] = "hybrid"
        updates[:external_id] = result[:docid] if profile.external_id&.start_with?("internal_")
      end

      profile.update!(updates)
    rescue => e
      Rails.logger.error "[LoadMoreCandidatesJob] Failed to merge profile #{profile.id}: #{e.message}"
    end

    def merge_arrays(arr1, arr2)
      return arr2 if arr1.blank?
      return arr1 if arr2.blank?
      (arr1 + arr2).uniq
    end

    def create_new_profile(account, result, profile_data, primary_email, all_emails, primary_phone, all_phones)
      curriculum_text = build_curriculum_text(profile_data, result)
      SourcedProfile.create!(
        account: account,
        sourcing_id: nil,
        uid: SecureRandom.uuid,
        provider: "pearch",
        external_id: result[:docid],
        linkedin_slug: profile_data[:linkedin_slug],
        linkedin_url: profile_data[:linkedin_url],
        name: profile_data[:name],
        first_name: profile_data[:first_name],
        middle_name: profile_data[:middle_name],
        last_name: profile_data[:last_name],
        email: primary_email,
        emails: all_emails,
        phone: primary_phone,
        phones: all_phones,
        date_birth: parse_date(profile_data[:date_birth]),
        title: profile_data[:title],
        role_name: profile_data[:role_name].presence || profile_data[:title],
        summary: profile_data[:summary],
        curriculum_text: curriculum_text,
        picture_url: profile_data[:picture_url],
        estimated_age: profile_data[:estimated_age],
        location: profile_data[:location],
        city: profile_data[:city],
        state: profile_data[:state],
        country: profile_data[:country],
        remote_work: profile_data[:remote_work],
        mobility: profile_data[:mobility],
        current_company: extract_current_company(profile_data),
        current_title: extract_current_title(profile_data),
        position_level: profile_data[:position_level],
        total_experience_years: profile_data[:total_experience_years],
        is_decision_maker: profile_data[:is_decision_maker] || false,
        is_top_universities: profile_data[:is_top_universities] || false,
        expertise: profile_data[:expertise] || [],
        languages_data: profile_data[:languages] || [],
        skills_data: profile_data[:skills] || [],
        has_emails: primary_email.present?,
        has_phone_numbers: primary_phone.present?,
        followers_count: profile_data[:followers_count],
        connections_count: profile_data[:connections_count],
        profile_data: profile_data,
        experiences_data: profile_data[:experiences] || [],
        educations_data: profile_data[:educations] || [],
        certifications_data: profile_data[:certifications] || [],
        awards_data: profile_data[:awards] || [],
        status: "new",
        profile_updated_at: Time.current
      )
    end

    def create_or_update_sourced_profile_sourcing(profile, sourcing, result)
      SourcedProfileSourcing.find_or_create_by!(
        sourced_profile_id: profile.id,
        sourcing_id: sourcing.id,
        account_id: sourcing.account_id,
        user_id: sourcing.user_id
      ) do |sps|
        sps.is_deleted = false
      end
    rescue => e
      Rails.logger.error "[LoadMoreCandidatesJob] Failed to link profile #{profile.id} to sourcing #{sourcing.id}: #{e.message}"
      nil
    end

    def extract_current_company(profile_data)
      find_current_experience(profile_data)&.dig(:company_info, :name)
    end

    def extract_current_title(profile_data)
      find_current_role(profile_data)&.dig(:title)
    end

    def build_curriculum_text(profile_data, result)
      SourcedProfiles::CurriculumTextBuilder.build(profile_data: profile_data, result: result)
    end

    def find_current_experience(profile_data)
      (profile_data[:experiences] || []).find do |exp|
        has_current_role?(exp)
      end
    end

    def find_current_role(profile_data)
      (profile_data[:experiences] || []).each do |exp|
        role = (exp[:company_roles] || []).find { |r| r[:is_current_experience] }
        return role if role
      end
      nil
    end

    def has_current_role?(experience)
      (experience[:company_roles] || []).any? { |role| role[:is_current_experience] }
    end

    def parse_date(date_string)
      return nil if date_string.blank?
      Date.parse(date_string)
    rescue StandardError
      nil
    end

    def load_candidates_in_order(ids)
      return [] if ids.blank?

      candidates_by_id = Candidate.where(id: ids).index_by(&:id)
      ids.filter_map { |id| candidates_by_id[id] }
    end

    def handle_error(account_id, user_id, sourcing_id, exception)
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "❌ [LoadMoreCandidatesJob] Failed"
      Rails.logger.error "   Account: #{account_id} | User: #{user_id} | Sourcing: #{sourcing_id}"
      Rails.logger.error "   Error: #{exception.message}"
      Rails.logger.error exception.backtrace.first(5).join("\n")
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      Apartment::Tenant.switch(Account.find(account_id).tenant) do
        sourcing = Sourcing.find_by(id: sourcing_id)
        return unless sourcing

        SourcingChannel.broadcast_to(
          "#{user_id}_sourcing_#{sourcing.id}",
          {
            type: "load_more_failed",
            sourcing_id: sourcing.id,
            error: exception.message,
            timestamp: Time.current.iso8601
          }
        )
      end
    end

    def broadcast_load_more_started(sourcing, page, page_size)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "load_more_started",
          sourcing_id: sourcing.id,
          page: page,
          page_size: page_size,
          timestamp: Time.current.iso8601,
          message: "Carregando mais candidatos da página #{page}..."
        }
      )
    rescue => e
      Rails.logger.error("[LoadMoreCandidatesJob] Failed to broadcast load_more_started: #{e.message}")
    end

    def broadcast_processing_source(sourcing, source, count)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "load_more_processing_source",
          sourcing_id: sourcing.id,
          source: source,
          count: count,
          timestamp: Time.current.iso8601,
          message: "Processando #{count} candidatos (#{source})..."
        }
      )
    rescue => e
      Rails.logger.error("[LoadMoreCandidatesJob] Failed to broadcast processing_source: #{e.message}")
    end

    def broadcast_load_more_profile_processed(sourcing, profile_id, _current, _total, _source)
      sps = SourcedProfileSourcing.find_by(
        sourcing_id: sourcing.id,
        sourced_profile_id: profile_id,
        is_deleted: false
      )
      return unless sps

      Sourcings::ProfileAnalyzedBroadcast.call(sourcing: sourcing, sourced_profile_sourcing: sps)
    rescue => e
      Rails.logger.error("[LoadMoreCandidatesJob] Failed to broadcast load_more profile row: #{e.message}")
    end
  end
end
