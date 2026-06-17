# frozen_string_literal: true

module Candidates
  module SearchProcessing
    extend ActiveSupport::Concern

    private

    def process_candidates_batch(candidates, sourcing, account, user, search_meta_by_id: {})
      total = candidates.size

      broadcast_profiles_processing_started(sourcing)

      processed_count = 0
      failed_count = 0

      candidates.each_with_index do |candidate, index|
        search_meta = search_meta_by_id[candidate.id] || {}

        log_candidate_processing(candidate, index, total, search_meta)

        profile = create_or_update_sourced_profile(sourcing, candidate, account, user, search_meta: search_meta)

        if profile
          processed_count += 1
          log_profile_created(profile)
          broadcast_profile_processed(sourcing, profile.id, processed_count, total)
        else
          failed_count += 1
          log_profile_failed(candidate)
        end
      rescue => e
        failed_count += 1
        log_candidate_error(candidate, e)
      end

      log_processing_summary(processed_count, failed_count)
      processed_count
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
      Rails.logger.info "🔗 [SearchProcessing] LINKING EXISTING PROFILE"
      Rails.logger.info "   Profile ID: #{profile.id} | Provider: #{profile.provider} | Sourcing ID: #{sourcing.id}"

      update_profile_from_candidate(profile, candidate) if profile.provider == "pearch"

      sps = SourcedProfileSourcing.find_or_create_by!(
        sourced_profile_id: profile.id,
        sourcing_id: sourcing.id,
        account_id: account.id,
        user_id: user.id
      ) do |new_sps|
        new_sps.is_deleted = false
        new_sps.search_source = search_meta[:source] if search_meta[:source].present?
        new_sps.search_score = search_meta[:score] if search_meta[:score].present?
      end

      update_sps_search_meta(sps, search_meta)

      profile
    end

    def update_sps_search_meta(sps, search_meta)
      return if search_meta.blank?

      attrs = {}
      attrs[:search_source] = search_meta[:source] if search_meta[:source].present?
      attrs[:search_score] = search_meta[:score] if search_meta[:score].present?
      sps.update!(attrs) if attrs.any?
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
        behavioral_skills_list: SourcedProfile.behavioral_skills_list_from_candidate(candidate),
        profile_updated_at: Time.current
      }

      updates[:provider] = "hybrid" if profile.provider == "pearch"

      profile.update!(updates)
    rescue => e
      Rails.logger.error("Failed to update profile #{profile.id} from candidate: #{e.message}")
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

      safely_enrich_profile(profile, candidate)
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
    rescue => e
      Rails.logger.error("[SearchProcessing] Failed to create sourced profile for candidate #{candidate.id}: #{e.message}")
      Rails.logger.error(e.backtrace.first(5).join("\n"))
      raise
    end

    def safely_enrich_profile(profile, candidate)
      SourcedProfiles::CandidateEnrichmentService.call(profile, candidate)
    rescue => e
      Rails.logger.error("[SearchProcessing] CandidateEnrichmentService failed for candidate #{candidate.id}: #{e.message}")
      Rails.logger.error(e.backtrace.first(5).join("\n"))
    end

    def build_linkedin_url(candidate)
      slug = candidate.linkedin_slug.presence || candidate.linkedin
      return nil if slug.blank?
      return slug if slug.start_with?("http")

      "https://linkedin.com/in/#{slug}"
    end

    def broadcast_profiles_processing_started(sourcing)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "profiles_processing_started",
          sourcing_id: sourcing.id,
          total_profiles: sourcing.local_results_count.to_i + sourcing.global_results_count.to_i
        }
      )
    end

    def broadcast_profiles_processing_completed(sourcing, total_processed)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "profiles_processing_completed",
          sourcing_id: sourcing.id,
          total_profiles_processed: total_processed
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

    def broadcast_load_more_completed(sourcing, loaded, page, total_pages, total_in_pool)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "load_more_completed",
          sourcing_id: sourcing.id,
          loaded: loaded,
          page: page,
          total_pages: total_pages,
          total_in_pool: total_in_pool,
          has_more: page < total_pages
        }
      )
    end

    def broadcast_pool_expired(sourcing)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        { type: "sourcing_pool_expired", sourcing_id: sourcing.id }
      )
    end

    def broadcast_profile_processed(sourcing, profile_id, _current, _total)
      sps = SourcedProfileSourcing.find_by(
        sourcing_id: sourcing.id,
        sourced_profile_id: profile_id,
        is_deleted: false
      )
      return unless sps

      Sourcings::ProfileAnalyzedBroadcast.call(sourcing: sourcing, sourced_profile_sourcing: sps)
    rescue => e
      Rails.logger.error("[SearchProcessing] Failed to broadcast profile processed: #{e.message}")
    end

    def log_candidate_processing(candidate, index, total, search_meta)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [SearchProcessing] PROCESSING CANDIDATE #{index + 1}/#{total}"
      Rails.logger.info "   Candidate ID: #{candidate.id}"
      Rails.logger.info "   Search source: #{search_meta[:source]} | Score: #{search_meta[:score]}" if search_meta.present?
    end

    def log_profile_created(profile)
      Rails.logger.info "✅ [SearchProcessing] Profile created/linked: #{profile.id}"
      Rails.logger.info "   Provider: #{profile.provider} | Curriculum present? #{profile.curriculum_text.present?}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def log_profile_failed(candidate)
      Rails.logger.error "❌ [SearchProcessing] Failed to create/link profile for candidate #{candidate.id}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def log_candidate_error(candidate, error)
      Rails.logger.error "❌ [SearchProcessing] Error processing candidate #{candidate.id}: #{error.message}"
      Rails.logger.error error.backtrace.first(5).join("\n")
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def log_processing_summary(processed, failed)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [SearchProcessing] Batch complete: #{processed} succeeded, #{failed} failed"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end
  end
end
