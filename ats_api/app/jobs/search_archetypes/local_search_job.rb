module SearchArchetypes
  class LocalSearchJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform(account_id, user_id, sourcing_id, archetype_id, profile = "balanced", additional_options = {})
      @account = Account.find(account_id)
      @user = User.find(user_id)

      Current.user = @user
      Current.account = @account

      Apartment::Tenant.switch(@account.tenant) do
        execute_search(sourcing_id, archetype_id, profile, additional_options)
      end
    rescue => e
      handle_error(account_id, sourcing_id, e)
    end

    private

    def execute_search(sourcing_id, archetype_id, profile, additional_options)
      sourcing = Sourcing.find(sourcing_id)
      archetype = SearchArchetype.find(archetype_id)

      sourcing.update!(status: "processing")
      broadcast_sourcing_started(sourcing)

      search_params = SearchArchetypes::ToLocalSearchService.call(
        archetype: archetype,
        profile: profile,
        additional_options: additional_options
      )

      if search_params[:use_hybrid]
        execute_hybrid_search(sourcing, archetype, search_params)
      else
        execute_legacy_search(sourcing, search_params)
      end

      sourcing.update!(status: "done")
      broadcast_sourcing_completed(sourcing)
    end

    def execute_hybrid_search(sourcing, archetype, search_params)
      service = Candidates::Search::HybridSearchService.new(
        account_id: @account.id,
        tenant: @account.tenant
      )

      user_filters = build_hybrid_filters(search_params[:where_filters])

      result = service.search(
        search_params[:search_text],
        user_filters: user_filters,
        limit: search_params[:limit]
      )

      store_search_metadata(sourcing, result, archetype)
      search_meta_by_id = result.search_meta_by_id || {}
      all_candidates = result.candidates
      candidate_ids = all_candidates.map(&:id)
      page_size = Sourcings::FirstBatchPageSize.for_sourcing(sourcing)
      pool_ttl = Candidates::LocalSearchJob::POOL_TTL

      Rails.cache.write(
        "sourcing_pool:#{sourcing.id}:local",
        {
          candidate_ids: candidate_ids,
          search_meta_by_id: search_meta_by_id,
          total: candidate_ids.size,
          page_size: page_size,
          created_at: Time.current.iso8601,
          expires_at: pool_ttl.from_now.iso8601
        },
        expires_in: pool_ttl
      )
      Rails.cache.write("sourcing_pool_page:#{sourcing.id}", 1, expires_in: pool_ttl)

      first_batch = all_candidates.first(page_size)
      first_batch_meta = search_meta_by_id.slice(*first_batch.map(&:id))

      sourcing.update!(
        results_count: first_batch.size,
        local_results_count: first_batch.size
      )

      broadcast_sourcing_profiles_found(sourcing, first_batch.size, "local")

      process_candidates(first_batch, sourcing, @account, @user, search_meta_by_id: first_batch_meta)
    end

    def execute_legacy_search(sourcing, search_params)
      Candidates::LocalSearchJob.perform_async(
        @account.id,
        @user.id,
        sourcing.id,
        search_params[:search_text],
        search_params[:where_filters].to_json,
        search_params[:filter_json],
        search_params[:order_json],
        search_params[:max_pages]
      )
    end

    def build_hybrid_filters(where_filters)
      filters = {}

      where_filters.each do |key, value|
        next if key == :is_deleted

        if value.is_a?(Hash)
          filters[key] = extract_filter_value(value)
        else
          filters[key] = value
        end
      end

      filters
    end

    def extract_filter_value(hash_value)
      return hash_value[:in] if hash_value.key?(:in)
      return hash_value[:gte] if hash_value.key?(:gte)
      return hash_value[:lte] if hash_value.key?(:lte)
      return hash_value[:ilike]&.gsub("%", "") if hash_value.key?(:ilike)
      return !hash_value[:not].nil? if hash_value.key?(:not)

      hash_value
    end

    def store_search_metadata(sourcing, result, archetype)
      sourcing.update!(
        search_metadata: {
          hybrid_search: true,
          archetype_id: archetype.id,
          archetype_name: archetype.name,
          request_id: result.metadata[:request_id],
          total_found: result.metadata[:count],
          fallback: result.metadata[:fallback],
          timestamp: Time.current.iso8601
        }.merge(result.metadata).to_json,
        search_explanation: result.explanation&.to_json
      )
    end

    def process_candidates(candidates, sourcing, account, user, search_meta_by_id: {})
      total = candidates.size

      candidates.each_with_index do |candidate, index|
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "🔄 [SearchArchetypes::LocalSearchJob] PROCESSING #{index + 1}/#{total}"
        Rails.logger.info "   Candidate ID: #{candidate.id}"

        search_meta = search_meta_by_id[candidate.id] || {}
        Rails.logger.info "   Search source: #{search_meta[:source]} | Search score: #{search_meta[:score]}" if search_meta.present?

        profile = create_or_update_sourced_profile(sourcing, candidate, account, user, search_meta: search_meta)

        if profile
          Rails.logger.info "✅ Profile created/linked: #{profile.id}"
        else
          Rails.logger.error "❌ Failed to create/link profile"
        end
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      end

      broadcast_local_search_completed(sourcing, total)
    end

    def create_or_update_sourced_profile(sourcing, candidate, account, user, search_meta: {})
      existing = sourcing.sourced_profiles.find_by(candidate_id: candidate.id)
      return existing if existing

      existing_profile = find_existing_profile(candidate, account)
      return link_existing_profile(existing_profile, sourcing, candidate, account, user, search_meta: search_meta) if existing_profile

      create_sourced_profile(sourcing, candidate, account, search_meta: search_meta)
    end

    def find_existing_profile(candidate, account)
      matcher = SourcedProfiles::ProfileMatchingService.new(account_id: account.id)
      matcher.find_duplicate(
        email: candidate.email,
        phone: candidate.phone || candidate.mobile_phone,
        cpf: candidate.cpf,
        linkedin_url: build_linkedin_url(candidate)
      )
    end

    def link_existing_profile(profile, sourcing, candidate, account, user, search_meta: {})
      if profile.provider == "pearch"
        update_profile_from_candidate(profile, candidate)
      end

      sps = SourcedProfileSourcing.find_or_create_by!(
        sourced_profile_id: profile.id,
        sourcing_id: sourcing.id,
        account_id: account.id,
        user_id: user.id
      ) do |sps|
        sps.is_deleted = false
        sps.search_source = search_meta[:source] if search_meta[:source].present?
        sps.search_score = search_meta[:score] if search_meta[:score].present?
      end
      if search_meta.present?
        attrs = {}
        attrs[:search_source] = search_meta[:source] if search_meta[:source].present?
        attrs[:search_score] = search_meta[:score] if search_meta[:score].present?
        sps.update!(attrs) if attrs.any?
      end

      profile
    end

    def update_profile_from_candidate(profile, candidate)
      return unless candidate.present?

      phone = candidate.phone || candidate.mobile_phone
      updates = {
        email: candidate.email.presence || profile.email,
        phone: phone.presence || profile.phone,
        cpf: candidate.cpf.presence || profile.cpf,
        date_birth: candidate.date_birth || profile.date_birth,
        picture_url: candidate.avatar_public_url.presence || profile.picture_url,
        summary: candidate.self_introduction.presence || profile.summary,
        curriculum_text: candidate.curriculum_text.presence || profile.curriculum_text,
        city: candidate.city.presence || profile.city,
        state: candidate.state.presence || profile.state,
        country: candidate.country.presence || profile.country,
        has_emails: (candidate.email.presence || profile.email).present?,
        has_phone_numbers: (phone.presence || profile.phone).present?,
        profile_updated_at: Time.current
      }

      updates[:provider] = "hybrid" if profile.provider == "pearch"

      profile.update!(updates)
    rescue => e
      Rails.logger.error("Failed to update profile #{profile.id}: #{e.message}")
    end

    def create_sourced_profile(sourcing, candidate, account, search_meta: {})
      phone = candidate.phone || candidate.mobile_phone

      profile = SourcedProfile.new(
        sourcing: sourcing,
        account: account,
        candidate: candidate,
        uid: SecureRandom.uuid,
        provider: "local",
        external_id: "internal_#{sourcing.id}_#{candidate.id}",
        linkedin_url: build_linkedin_url(candidate),
        name: candidate.name,
        email: candidate.email,
        curriculum_text: candidate.curriculum_text,
        phone: phone,
        cpf: candidate.cpf,
        date_birth: candidate.date_birth,
        title: candidate.role_name,
        summary: candidate.self_introduction,
        picture_url: candidate.avatar_public_url,
        gender: candidate.gender,
        marital_status: candidate.marital_status,
        location: [ candidate.city, candidate.state ].compact.join(", "),
        city: candidate.city,
        state: candidate.state,
        country: candidate.country,
        remote_work: candidate.remote_work,
        mobility: candidate.mobility,
        current_company: candidate.current_company,
        current_title: candidate.role_name,
        role_name: candidate.role_name,
        position_level: candidate.position_level,
        has_emails: candidate.email.present?,
        has_phone_numbers: phone.present?,
        status: "new"
      )

      SourcedProfiles::CandidateEnrichmentService.call(profile, candidate)
      profile.save!

      SourcedProfileSourcing.create!(
        sourced_profile_id: profile.id,
        sourcing_id: sourcing.id,
        account_id: account.id,
        user_id: sourcing.user_id,
        is_deleted: false,
        search_source: search_meta[:source],
        search_score: search_meta[:score]
      )

      profile
    end

    def build_linkedin_url(candidate)
      slug = candidate.linkedin_slug.presence || candidate.linkedin
      return nil if slug.blank?
      return slug if slug.start_with?("http")

      "https://linkedin.com/in/#{slug}"
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

    def broadcast_sourcing_profiles_found(sourcing, count, source)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_profiles_found",
          sourcing_id: sourcing.id,
          count: count,
          source: source,
          total_expected: sourcing.local_results_count.to_i + sourcing.global_results_count.to_i
        }
      )
    end

    def broadcast_local_search_completed(sourcing, count)
      sleep(0.3)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "local_profiles_created",
          sourcing_id: sourcing.id,
          profiles_count: count,
          source: "local",
          phase: "creation_completed",
          timestamp: Time.current.iso8601
        }
      )
      Rails.logger.info "✅ [SearchArchetypes::LocalSearchJob] Local search completed - #{count} profiles created"

      # Enviar sinal para indicar que está pronto para análise IA
      sleep(0.2)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "profiles_processing_started",
          sourcing_id: sourcing.id,
          total_profiles: count,
          source: "local",
          phase: "ai_analysis_queue"
        }
      )
    end

    def handle_error(account_id, sourcing_id, exception)
      Rails.logger.error("[SearchArchetypes::LocalSearchJob] Failed: #{exception.message}")
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
