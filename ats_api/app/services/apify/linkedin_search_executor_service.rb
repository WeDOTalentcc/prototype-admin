# frozen_string_literal: true

module Apify
  class LinkedinSearchExecutorService
    DEFAULT_MODE = :full_with_email
    DEFAULT_PAGES = 2
    MAX_PAGES = 10

    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 5 # seconds, doubles each attempt

    RETRYABLE_ERRORS = [
      LinkedinSearchService::TimeoutError,
      LinkedinSearchService::RunFailedError,
      LinkedinSearchService::AbortedError
    ].freeze

    ADVANCED_PARAM_KEYS = %i[
      seniority_levels functions company_headcount profile_languages
      first_names last_names company_headquarter_locations
      years_at_current_company
    ].freeze

    EXCLUSION_PARAM_KEYS = %i[
      exclude_locations exclude_current_companies exclude_past_companies
      exclude_schools exclude_current_job_titles exclude_past_job_titles
      exclude_industry_ids exclude_seniority_levels exclude_function_ids
      exclude_company_headquarter_locations
    ].freeze

    def initialize(user:, sourcing:, params: {})
      @user = user
      @account = user.account
      @sourcing = sourcing
      @params = params
    end

    def call
      options = build_search_options
      result_set = search_with_retry(options)

      profiles = create_sourced_profiles(result_set)
      update_sourcing(result_set, profiles)

      { success: true, sourcing_id: @sourcing.id, profiles_count: profiles.size, total_found: result_set.total_count }
    rescue LinkedinSearchService::RateLimitError => e
      handle_rate_limit(e)
    rescue *RETRYABLE_ERRORS => e
      handle_error("LinkedIn search failed após #{MAX_RETRIES} tentativas: #{e.message}")
    rescue StandardError => e
      handle_error(e.message)
    end

    private

    def search_with_retry(options)
      attempt = 0
      begin
        attempt += 1
        LinkedinSearchService.new.search(**options)
      rescue *RETRYABLE_ERRORS => e
        if attempt < MAX_RETRIES
          delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
          Rails.logger.warn "[Apify::LinkedinSearchExecutor] Tentativa #{attempt}/#{MAX_RETRIES} falhou (#{e.class.name}): #{e.message}. Retry em #{delay}s"
          sleep delay
          retry
        end
        raise
      end
    end

    def build_search_options
      options = { mode: search_mode }
      query_text = @params[:query].presence || @sourcing.query

      options[:search_query] = query_text if query_text.present?
      options[:current_job_titles] = Array(@params[:current_job_titles]) if @params[:current_job_titles].present?
      options[:past_job_titles] = Array(@params[:past_job_titles]) if @params[:past_job_titles].present?
      options[:locations] = Array(@params[:locations].presence || ["Brazil"])
      options[:current_companies] = Array(@params[:current_companies]) if @params[:current_companies].present?
      options[:past_companies] = Array(@params[:past_companies]) if @params[:past_companies].present?
      options[:schools] = Array(@params[:schools]) if @params[:schools].present?
      options[:industries] = Array(@params[:industries]) if @params[:industries].present?
      options[:years_of_experience] = Array(@params[:years_of_experience]) if @params[:years_of_experience].present?
      options[:take_pages] = (@params[:take_pages] || DEFAULT_PAGES).to_i.clamp(1, MAX_PAGES)
      options[:max_items] = (@params[:max_items] || 50).to_i

      append_advanced_params!(options)
      append_exclusion_params!(options)

      options
    end

    def search_mode
      (@params[:mode] || DEFAULT_MODE).to_sym
    end

    def create_sourced_profiles(result_set)
      matcher = SourcedProfiles::ProfileMatchingService.new(account_id: @account.id)

      result_set.filter_map do |profile|
        existing = matcher.find_duplicate(
          email: profile.email,
          linkedin_url: profile.linkedin_url
        )

        if existing
          update_existing_profile(existing, profile)
          link_to_sourcing(existing, profile)
          existing
        else
          sourced = create_new_profile(profile)
          link_to_sourcing(sourced, profile)
          sourced
        end
      rescue Apify::LinkedinSearchService::Profile::ParseError => e
        Rails.logger.warn "[Apify::LinkedinSearchExecutor] Perfil descartado — dados obrigatorios ausentes: #{e.message}"
        nil
      rescue StandardError => e
        Rails.logger.error "[Apify::LinkedinSearchExecutor] Falha ao processar perfil #{profile.full_name}: #{e.message}"
        nil
      end
    end

    def create_new_profile(profile)
      SourcedProfile.create!(
        account: @account,
        uid: SecureRandom.uuid,
        provider: "linkedin",
        external_id: profile.public_identifier,
        name: profile.full_name,
        first_name: profile.first_name,
        last_name: profile.last_name,
        title: profile.headline,
        current_company: profile.current_company,
        email: profile.email,
        emails: [profile.email].compact,
        has_emails: profile.has_email?,
        linkedin_url: profile.linkedin_url,
        linkedin_slug: profile.public_identifier,
        city: profile.location.city,
        state: profile.location.state,
        country: profile.location.country,
        location: profile.location.to_s,
        total_experience_years: profile.years_of_experience,
        skills_data: profile.skills,
        languages_data: profile.languages,
        picture_url: profile.photo_url,
        summary: profile.about,
        current_title: profile.current_position&.title,
        followers_count: profile.follower_count,
        connections_count: profile.connections_count,
        certifications_data: profile.certifications.map(&:to_h),
        awards_data: profile.honors_and_awards,
        experiences_data: profile.experience.map { |e| experience_to_hash(e) },
        educations_data: profile.education.map { |e| education_to_hash(e) },
        curriculum_text: build_curriculum_text(profile),
        profile_data: build_profile_data(profile),
        status: "new"
      )
    end

    def update_existing_profile(existing, profile)
      existing.update!(
        name: profile.full_name.presence || existing.name,
        title: profile.headline.presence || existing.title,
        current_company: profile.current_company.presence || existing.current_company,
        email: profile.email.presence || existing.email,
        linkedin_url: profile.linkedin_url.presence || existing.linkedin_url,
        linkedin_slug: profile.public_identifier.presence || existing.linkedin_slug,
        city: profile.location.city.presence || existing.city,
        state: profile.location.state.presence || existing.state,
        country: profile.location.country.presence || existing.country,
        total_experience_years: profile.years_of_experience || existing.total_experience_years,
        picture_url: profile.photo_url.presence || existing.picture_url,
        summary: profile.about.presence || existing.summary,
        followers_count: profile.follower_count || existing.followers_count,
        connections_count: profile.connections_count || existing.connections_count,
        certifications_data: profile.certifications.present? ? profile.certifications.map(&:to_h) : existing.certifications_data,
        awards_data: profile.honors_and_awards.present? ? profile.honors_and_awards : existing.awards_data,
        profile_data: build_profile_data(profile),
        profile_updated_at: Time.current
      )
    end

    def link_to_sourcing(sourced_profile, profile)
      SourcedProfileSourcing.find_or_create_by!(
        sourced_profile: sourced_profile,
        sourcing: @sourcing
      ) do |sps|
        sps.account = @account
        sps.user = @user
        sps.search_source = "linkedin"
      end
    end

    def update_sourcing(result_set, profiles)
      @sourcing.update!(
        status: "done",
        results_count: profiles.size,
        global_results_count: result_set.total_count,
        processed_count: profiles.size,
        duration: 0,
        response_metadata: {
          run_id: result_set.run_id,
          pages_scraped: result_set.pages_scraped,
          has_more: result_set.has_more?,
          estimated_cost: result_set.query.estimated_cost
        }
      )
    end

    def experience_to_hash(exp)
      {
        title: exp.title,
        company: exp.company,
        company_url: exp.company_url,
        company_id: exp.company_id,
        company_universal_name: exp.company_universal_name,
        location: exp.location,
        employment_type: exp.employment_type,
        workplace_type: exp.workplace_type,
        duration: exp.duration,
        description: exp.description,
        current: exp.current?,
        start_date: exp.start_date,
        end_date: exp.end_date,
        skills: exp.skills
      }.compact
    end

    def education_to_hash(edu)
      {
        school: edu.school,
        school_linkedin_url: edu.school_linkedin_url,
        school_id: edu.school_id,
        degree: edu.degree,
        field: edu.field,
        description: edu.description,
        start_date: edu.start_date,
        end_date: edu.end_date,
        period: edu.period,
        skills: edu.skills
      }.compact
    end

    def build_curriculum_text(profile)
      parts = [
        profile.full_name,
        profile.headline,
        profile.about,
        profile.experience.map { |e| "#{e.title} at #{e.company}" }.join("; "),
        profile.education.map { |e| "#{e.degree} #{e.field} at #{e.school}" }.join("; "),
        profile.skills.join(", "),
        profile.certifications.map(&:name).join(", ")
      ]
      parts.compact_blank.join("\n")
    end

    def build_profile_data(profile)
      {
        open_to_work: profile.open_to_work?,
        hiring: profile.hiring?,
        premium: profile.premium?,
        influencer: profile.influencer?,
        verified: profile.verified?,
        registered_at: profile.registered_at,
        top_skills_text: profile.top_skills_text,
        object_urn: profile.object_urn,
        profile_picture: profile.profile_picture,
        cover_picture: profile.cover_picture,
        projects: profile.projects.map(&:to_h),
        volunteering: profile.volunteering.map(&:to_h),
        publications: profile.publications.map(&:to_h),
        courses: profile.courses,
        patents: profile.patents,
        causes: profile.causes,
        received_recommendations: profile.received_recommendations,
        more_profiles: profile.more_profiles
      }.compact
    end

    def append_advanced_params!(options)
      ADVANCED_PARAM_KEYS.each do |key|
        value = @params[key]
        next if value.nil?

        options[key] = value.is_a?(Array) ? value : Array(value)
      end

      options[:recently_changed_jobs] = @params[:recently_changed_jobs] unless @params[:recently_changed_jobs].nil?
      options[:auto_query_segmentation] = @params[:auto_query_segmentation] unless @params[:auto_query_segmentation].nil?
    end

    def append_exclusion_params!(options)
      EXCLUSION_PARAM_KEYS.each do |key|
        value = @params[key]
        next if value.nil?

        options[key] = value.is_a?(Array) ? value : Array(value)
      end
    end

    def handle_rate_limit(error)
      @sourcing.update!(status: "failed", response_metadata: { error: "rate_limited", retry_after: error.retry_after&.iso8601 })
      { success: false, error: "LinkedIn rate limit. Retry in #{error.minutes_until_retry} minutes.", retry_after: error.retry_after }
    end

    def handle_error(message)
      Rails.logger.error "[Apify::LinkedinSearchExecutor] #{message}"
      @sourcing.update!(status: "failed", response_metadata: { error: message })
      { success: false, error: message }
    end
  end
end
