# frozen_string_literal: true

module Candidates
  class PromptSearchSourcingService
    PER_PAGE = 30
    ID_FIELDS = %w[id external_id].freeze

    def self.call(user:, account:, search: nil, where: {}, filter: {}, order: {})
      new(user: user, account: account, search: search, where: where, filter: filter, order: order).call
    end

    def initialize(user:, account:, search: nil, where: {}, filter: {}, order: {})
      @user = user
      @account = account
      @search = search || "*"
      @where = convert_to_hash(where)
      @filter = convert_to_hash(filter)
      @order = convert_to_hash(order)
    end

    def call
      sourcing = create_sourcing
      process_search_results(sourcing)
      sourcing.update!(status: "done", results_count: sourcing.sourced_profiles.count)
      sourcing
    rescue => e
      sourcing&.update!(status: "failed")
      Rails.logger.error("PromptSearchSourcingService failed: #{e.message}\n#{e.backtrace.join("\n")}")
      raise
    end

    private

    def convert_to_hash(value)
      return {} if value.blank?
      return value.to_unsafe_h if value.is_a?(ActionController::Parameters)
      return value.to_h if value.respond_to?(:to_h)
      value.is_a?(Hash) ? value : {}
    end

    def create_sourcing
      Apartment::Tenant.switch!(@account.tenant)

      Sourcing.create!(
        user_id: @user.id,
        account_id: @account.id,
        provider: "local",
        query: display_query,
        parameters: search_params_hash,
        status: "processing",
        searched_at: Time.current
      )
    end

    def display_query
      @search.present? && @search != "*" ? @search : "Internal search"
    end

    def search_params_hash
      { search: @search, where: @where, filter: @filter, order: @order }
    end

    def process_search_results(sourcing)
      total_processed = 0

      each_result_page do |records|
        records.each do |candidate|
          create_sourced_profile_from_candidate(sourcing, candidate)
          total_processed += 1
        end
      end

      Rails.logger.info("PromptSearchSourcingService: Processed #{total_processed} candidates for sourcing #{sourcing.id}")
    end

    def each_result_page
      page = 1

      loop do
        results = fetch_page_results(page)
        break if results[:records].empty?

        yield results[:records]

        break unless has_more_pages?(page, results[:total_count])
        page += 1
      end
    end

    def fetch_page_results(page)
      Candidate.search_default(
        @search,
        build_search_params(page),
        page,
        false,
        @user.id,
        false
      )
    end

    def has_more_pages?(current_page, total_count)
      return false if total_count.nil? || total_count.zero?
      current_page < (total_count.to_f / PER_PAGE).ceil
    end

    def build_search_params(page)
      params = base_search_params(page)
      apply_filters!(params) if @filter.present?
      params[:where] = params[:where].deep_symbolize_keys
      params
    end

    def base_search_params(page)
      {
        where: @where.dup,
        order: @order.dup,
        page: page,
        per_page: PER_PAGE
      }
    end

    def apply_filters!(params)
      @filter.each do |field, value|
        apply_filter_condition!(params, field, value)
      end
    end

    def apply_filter_condition!(params, field, value)
      return unless value.present?

      if value.is_a?(Array)
        apply_array_filter!(params, field, value)
      elsif value.is_a?(Integer) || value.is_a?(Hash)
        params[:where][field.to_s] = value
      else
        params[:where][field.to_s] = filter_value_for(field, value)
      end
    end

    def apply_array_filter!(params, field, values)
      return params[:where][field.to_s] = values unless values.all? { |v| v.is_a?(String) || v.is_a?(Numeric) }

      params[:where][:_or] ||= []
      values.each do |val|
        params[:where][:_or] << { field.to_s => filter_value_for(field, val) }
      end
    end

    def filter_value_for(field, value)
      return value.to_s.match?(/^\d+$/) ? value.to_i : value if id_field?(field)
      { like: "%#{value.to_s.downcase}%" }
    end

    def id_field?(field)
      ID_FIELDS.include?(field.to_s)
    end

    def create_sourced_profile_from_candidate(sourcing, candidate)
      existing = sourcing.sourced_profiles.find_by(candidate_id: candidate.id)
      return existing if existing

      existing_profile = find_existing_profile(sourcing, candidate)
      return link_existing_profile(existing_profile, sourcing) if existing_profile

      create_new_sourced_profile(sourcing, candidate)
    end

    def find_existing_profile(sourcing, candidate)
      SourcedProfile.find_existing_by_identity(
        external_id: nil,
        account_id: @account.id,
        cpf: candidate.cpf,
        email: candidate.email,
        linkedin_url: build_linkedin_url(candidate),
        phone: candidate.phone || candidate.mobile_phone
      )
    end

    def link_existing_profile(profile, sourcing)
      profile.ensure_sourced_profile_sourcing(sourcing, @account, @user)
      profile
    end

    def create_new_sourced_profile(sourcing, candidate)
      SourcedProfile.create!(
        sourcing: sourcing,
        account: @account,
        candidate: candidate,
        uid: SecureRandom.uuid,
        provider: "local",
        external_id: "internal_#{sourcing.id}_#{candidate.id}",
        **profile_attributes(candidate)
      )
    end

    def profile_attributes(candidate)
      phone = candidate.phone || candidate.mobile_phone

      {
        linkedin_slug: linkedin_slug(candidate),
        linkedin_url: build_linkedin_url(candidate),
        name: candidate.name,
        email: candidate.email,
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
        total_experience_years: calculate_total_experience(candidate),
        currency: candidate.currency,
        clt_expectation: candidate.clt_expectation,
        pj_expectation: candidate.pj_expectation,
        freelance_expectation: candidate.freelance_expectation,
        has_emails: candidate.email.present?,
        has_phone_numbers: phone.present?,
        skills_data: extract_skills(candidate),
        languages_data: extract_languages(candidate),
        experiences_data: extract_experiences(candidate),
        educations_data: extract_educations(candidate),
        profile_data: build_profile_data(candidate),
        status: "new",
        pin_user_ids: candidate.pin_user_ids || [],
        confidential_user_ids: candidate.confidential_user_ids || []
      }
    end

    def linkedin_slug(candidate)
      candidate.linkedin_slug.presence || candidate.linkedin
    end

    def build_linkedin_url(candidate)
      slug = linkedin_slug(candidate)
      return nil if slug.blank?
      return slug if slug.start_with?("http")
      "https://linkedin.com/in/#{slug}"
    end

    def extract_skills(candidate)
      candidate.skill_relationships.includes(:skill).map do |sr|
        { name: sr.skill&.name, level: sr.level_skill }.compact
      end
    end

    def extract_languages(candidate)
      candidate.language_relationships.includes(:language).map do |lr|
        { name: lr.language&.name, level: lr.level }.compact
      end
    end

    def extract_experiences(candidate)
      candidate.experiences.order(end_date: :desc).limit(10).map do |exp|
        {
          company: exp.company,
          role: exp.role,
          start_date: exp.start_date,
          end_date: exp.end_date,
          description: exp.description
        }
      end
    end

    def extract_educations(candidate)
      candidate.educations.order(end_date: :desc).limit(5).map do |edu|
        {
          institution: edu.institution&.name,
          education_level: map_formation_type(edu.formation_type),
          study_area: edu.study_area&.name,
          start_date: edu.start_date,
          end_date: edu.end_date
        }
      end
    rescue => e
      Rails.logger.error "[PromptSearchSourcingService] Error extracting educations: #{e.message}"
      []
    end

    def map_formation_type(type)
      return nil unless type

      case type.to_i
      when 1 then "Elementary School"
      when 2 then "High School"
      when 3 then "Technical"
      when 4 then "Associate Degree"
      when 5 then "Bachelor"
      when 6 then "Teaching Degree"
      when 7 then "Postgraduate"
      else nil
      end
    rescue
      nil
    end

    def build_profile_data(candidate)
      {
        candidate_id: candidate.id,
        source: "internal_search",
        created_at: candidate.created_at,
        updated_at: candidate.updated_at
      }
    end

    def calculate_total_experience(candidate)
      candidate.experiences.sum do |exp|
        next 0 unless exp.start_date
        years_between(exp.start_date, exp.end_date || Time.current)
      end
    end

    def years_between(start_date, end_date)
      ((end_date - start_date) / 1.year).to_i.abs
    end
  end
end
