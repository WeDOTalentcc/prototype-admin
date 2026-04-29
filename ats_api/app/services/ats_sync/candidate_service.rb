# frozen_string_literal: true

module AtsSync
  class CandidateService < BaseService
    LANGUAGE_LEVELS = {
      "básico" => "basic",
      "intermediário" => "intermediate",
      "avançado" => "advanced",
      "fluente" => "fluent",
      "nativo" => "native"
    }.freeze

    def self.sync(candidate)
      new(candidate).sync
    end

    private

    def ats_provider
      "questt"
    end

    def execute_sync(payload)
      return client.update_candidate(payload) if record.external_id.present?

      client.create_candidate(payload)
    end

    def validate_required_data
      return "candidate name missing" if record.name.blank?
      return "account not found" if record.account.blank?

      nil
    end

    def build_payload
      payload = {
        provider: ats_provider,
        account_id: record.account_id,
        references: build_references,
        ats_references: build_ats_references,
        candidate: build_candidate_data,
        experiences: build_experiences,
        educations: build_educations,
        skills: build_skills,
        languages: build_languages
      }

      payload[:action] = record.external_id.present? ? "update_candidate" : "create_candidate"

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "📦 FINAL PAYLOAD SUMMARY"
      Rails.logger.info "   Action: #{payload[:action]}"
      Rails.logger.info "   Candidate: #{payload[:candidate].keys.size} fields"
      Rails.logger.info "   Experiences: #{payload[:experiences].size}"
      Rails.logger.info "   Educations: #{payload[:educations].size}"
      Rails.logger.info "   Skills: #{payload[:skills].size}"
      Rails.logger.info "   Languages: #{payload[:languages].size}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      payload
    end

    def build_references
      {
        wedo_candidate_id: record.id,
        wedo_job_id: nil,
        wedo_apply_id: nil
      }
    end

    def build_ats_references
      refs = {}
      refs[:ats_candidate_id] = record.external_id if record.external_id.present?
      refs
    end

    def build_candidate_data
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "📦 [CandidateService] BUILDING CANDIDATE DATA FOR ATS"
      Rails.logger.info "   Candidate ID: #{record.id}"
      Rails.logger.info "   Name: #{record.name}"
      Rails.logger.info "   � email: #{record.email.inspect}"
      Rails.logger.info "   📱 mobile_phone: #{record.mobile_phone.inspect}"
      Rails.logger.info "   🔗 linkedin (from DB): #{record.linkedin.inspect}"
      Rails.logger.info "   🔗 linkedin (built): #{build_linkedin_url.inspect}"
      Rails.logger.info "   📍 current_company (from DB): #{record.current_company.inspect}"
      Rails.logger.info "   📍 role_name (from DB): #{record.role_name.inspect}"
      Rails.logger.info "   📍 title (from sourced_profile): #{sourced_profile_title.inspect}"

      payload = {
        name: record.name,
        email: record.email,
        mobile_phone: record.mobile_phone,
        phone: record.phone,
        secondary_email: record.secondary_email,
        linkedin: build_linkedin_url,
        github: record.github,
        portfolio: record.portfolio,
        current_company: record.current_company,
        role_name: record.role_name,
        title: sourced_profile_title,
        position_level: record.position_level,
        date_birth: record.date_birth,
        gender: record.gender,
        nationality: record.nationality,
        cpf: record.cpf,
        address: build_address,
        salary: build_salary,
        preferences: build_preferences,
        self_introduction: record.self_introduction,
        curriculum_text: record.curriculum_text,
        curriculum_pdf_url: curriculum_pdf_url,
        avatar_url: avatar_url,
        picture_url: picture_url
      }.compact

      Rails.logger.info "   📍 current_company (in payload): #{payload[:current_company].inspect}"
      Rails.logger.info "   📍 role_name (in payload): #{payload[:role_name].inspect}"
      Rails.logger.info "   📍 title (in payload): #{payload[:title].inspect}"
      Rails.logger.info "   📧 email (in payload): #{payload[:email].inspect}"
      Rails.logger.info "   📱 mobile_phone (in payload): #{payload[:mobile_phone].inspect}"
      Rails.logger.info "   🔗 linkedin (in payload): #{payload[:linkedin].inspect}"
      Rails.logger.info "   📦 Total fields in payload: #{payload.keys.size}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      payload
    end

    def build_address
      return nil unless record.city.present?

      {
        street: record.street,
        number: record.number,
        complement: record.complement,
        district: record.district,
        city: record.city,
        state: record.state,
        country: record.country || "Brasil",
        zip: record.zip
      }.compact
    end

    def build_salary
      {
        current: record.current_salary,
        clt_expectation: record.clt_expectation,
        pj_expectation: record.pj_expectation,
        currency: record.currency || "BRL"
      }.compact
    end

    def build_preferences
      {
        remote_work: record.remote_work,
        mobility: record.mobility,
        hiring_regimes: []
      }.compact
    end

    def build_experiences
      return [] unless record.respond_to?(:experiences)

      all_experiences = record.experiences.order(start_date: :desc).map do |exp|
        {
          wedo_id: exp.id,
          company: exp.company&.name,
          position: exp.occupation&.name,
          description: exp.description,
          start_date: format_date(exp.start_date),
          end_date: format_date(exp.end_date),
          is_current: exp.work_here
        }
      end

      experiences = all_experiences.uniq { |e| [ e[:company]&.downcase&.strip, e[:position]&.downcase&.strip ] }

      Rails.logger.info "   💼 Experiences built: #{experiences.size} unique (#{all_experiences.size} total)"
      experiences
    end

    def build_educations
      return [] unless record.respond_to?(:educations)

      all_educations = record.educations.order(start_date: :desc).map do |edu|
        {
          wedo_id: edu.id,
          institution: edu.institution&.name,
          degree: edu.formation_type,
          field: edu.study_area&.name,
          start_date: format_date(edu.start_date),
          end_date: format_date(edu.end_date),
          status: edu.study_here ? "in_progress" : "completed"
        }
      end

      educations = all_educations.uniq { |e| [ e[:institution]&.downcase&.strip, e[:field]&.downcase&.strip ] }

      Rails.logger.info "   🎓 Educations built: #{educations.size} unique (#{all_educations.size} total)"
      educations
    end

    def build_skills
      return [] unless record.respond_to?(:skill_relationships)

      skills = record.skill_relationships.includes(:skill).map do |skill_rel|
        {
          name: skill_rel.skill.name,
          level: skill_rel.level_skill
        }
      end

      Rails.logger.info "   🎯 Skills built: #{skills.size} skills"
      skills.each_with_index do |skill, idx|
        Rails.logger.info "      #{idx + 1}. #{skill[:name]} (level: #{skill[:level]})" if idx < 5
      end
      Rails.logger.info "      ... and #{skills.size - 5} more" if skills.size > 5

      skills
    end

    def build_languages
      return [] unless record.respond_to?(:language_relationships)

      languages = record.language_relationships.includes(:language).map do |lang_rel|
        {
          name: lang_rel.language.name,
          level: map_language_level_to_english(lang_rel.level)
        }.compact
      end

      Rails.logger.info "   🌍 Languages built: #{languages.size} languages"
      languages
    end

    def map_language_level_to_english(level)
      return nil if level.blank?

      LANGUAGE_LEVELS.fetch(level.to_s.downcase, nil)
    end

    def curriculum_pdf_url
      return nil unless record.curriculum_pdf.attached?

      Rails.application.routes.url_helpers.rails_blob_url(
        record.curriculum_pdf,
        host: ENV.fetch("APP_HOST", "http://localhost:3000")
      )
    rescue StandardError
      nil
    end

    def avatar_url
      return nil unless record.avatar.attached?

      Rails.application.routes.url_helpers.rails_blob_url(
        record.avatar,
        host: ENV.fetch("APP_HOST", "http://localhost:3000")
      )
    rescue StandardError
      nil
    end

    def picture_url
      return nil unless record.respond_to?(:sourced_profile)

      sourced_profile = record.sourced_profile.order(created_at: :desc).first
      sourced_profile&.picture_url
    end

    def sourced_profile_title
      return nil unless record.respond_to?(:sourced_profile)

      sourced_profile = record.sourced_profile.order(created_at: :desc).first
      sourced_profile&.title
    end

    def build_linkedin_url
      return record.linkedin if record.linkedin.present?
      return nil unless record.respond_to?(:sourced_profile)

      sourced_profile = record.sourced_profile.order(created_at: :desc).first
      return nil unless sourced_profile

      linkedin_slug = sourced_profile.linkedin_slug || sourced_profile.external_id
      return nil if linkedin_slug.blank?

      "https://www.linkedin.com/in/#{linkedin_slug}"
    end

    def format_date(value)
      return nil if value.blank?

      value.to_date.iso8601
    end

    def save_ats_ids(ats_ids)
      return unless ats_ids.present?

      updates = {}

      if ats_ids["candidate_id"]
        updates[:external_id] = ats_ids["candidate_id"]
        updates[:external_provider] = "questt"
      end

      record.update_columns(updates) if updates.any?

      save_nested_ids(ats_ids)
    end

    def save_nested_ids(ats_ids)
    end
  end
end
