# frozen_string_literal: true

module SourcedProfiles
  class ConvertToCandidateService
    attr_reader :sourced_profile, :errors

    def self.call(sourced_profile_ids)
      new(sourced_profile_ids).call
    end

    def initialize(sourced_profile_ids)
      @sourced_profile_ids = Array(sourced_profile_ids)
      @errors = []
      @success_count = 0
      @skipped_count = 0
    end

    def call
      @sourced_profile_ids.each do |id|
        process_profile(id)
      end

      {
        success: @errors.empty?,
        converted: @success_count,
        skipped: @skipped_count,
        failed: @errors.size,
        errors: @errors
      }
    end

    private

    def process_profile(id)
      sourced_profile = SourcedProfile.find(id)

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [ConvertToCandidateService] PROCESS PROFILE START"
      Rails.logger.info "   SourcedProfile ID: #{sourced_profile.id}"
      Rails.logger.info "   Already imported?: #{sourced_profile.imported?}"
      Rails.logger.info "   Candidate ID: #{sourced_profile.candidate_id.inspect}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      candidate = if sourced_profile.imported?
        Rails.logger.info "   🔍 Finding existing candidate: #{sourced_profile.candidate_id}"
        found = Candidate.find_by(id: sourced_profile.candidate_id)
        Rails.logger.info "   #{found ? '✅' : '❌'} Candidate found: #{found.inspect}"
        found
      else
        Rails.logger.info "   🆕 Creating new candidate"
        find_or_create_candidate(sourced_profile)
      end

      unless candidate
        Rails.logger.error "   ❌ No candidate found/created, aborting"
        return
      end

      Rails.logger.info "   ✅ Proceeding with candidate #{candidate.id}"
      Rails.logger.info "   Starting transaction to create relationships..."

      ActiveRecord::Base.transaction do
        Rails.logger.info "   📝 Creating skills..."
        create_skills(candidate, sourced_profile)

        Rails.logger.info "   📝 Creating educations..."
        create_educations(candidate, sourced_profile)

        Rails.logger.info "   📝 Creating experiences..."
        create_experiences(candidate, sourced_profile)

        Rails.logger.info "   📝 Creating languages..."
        create_languages(candidate, sourced_profile)

        sourced_profile.update!(candidate_id: candidate.id) unless sourced_profile.imported?
        @success_count += 1

        Rails.logger.info("✅ Successfully converted SourcedProfile #{id} to Candidate #{candidate.id}")
      end

      sync_pending_applies(candidate)
    rescue => e
      @errors << { sourced_profile_id: id, error: e.message }
      Rails.logger.error("Failed to convert SourcedProfile #{id}: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
    end

    def find_or_create_candidate(sourced_profile)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔍 [ConvertToCandidateService] FIND OR CREATE CANDIDATE"
      Rails.logger.info "   SourcedProfile ID: #{sourced_profile.id}"
      Rails.logger.info "   Name: #{sourced_profile.full_name}"
      Rails.logger.info "   📍 current_company (from sourced_profile): #{sourced_profile.current_company.inspect}"
      Rails.logger.info "   📍 current_title (from sourced_profile): #{sourced_profile.current_title.inspect}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      discover_email_if_needed(sourced_profile)

      candidate = find_existing_candidate(sourced_profile)

      if candidate
        Rails.logger.info "✅ [ConvertToCandidateService] Candidate already exists: #{candidate.id}"
        Rails.logger.info "   Current company (existing): #{candidate.current_company.inspect}"
        return candidate
      end

      candidate = Candidate.create!(
        account_id: sourced_profile.account_id,
        name: sourced_profile.full_name,
        email: extract_email(sourced_profile),
        mobile_phone: extract_phone(sourced_profile),
        phone: extract_phone(sourced_profile),
        cpf: sourced_profile.cpf,
        date_birth: sourced_profile.date_birth,
        gender: map_gender(sourced_profile.gender),
        marital_status: map_marital_status(sourced_profile.marital_status),
        city: sourced_profile.city,
        state: sourced_profile.state,
        country: sourced_profile.country,
        street: sourced_profile.street,
        number: sourced_profile.number,
        district: sourced_profile.district,
        complement: sourced_profile.complement,
        zip: sourced_profile.zip_code,
        nationality: sourced_profile.nationality,
        remote_work: sourced_profile.remote_work,
        mobility: sourced_profile.mobility,
        current_company: sourced_profile.current_company,
        role_name: sourced_profile.current_title,
        position_level: sourced_profile.position_level,
        currency: sourced_profile.currency,
        current_salary: sourced_profile.current_salary,
        desired_salary: sourced_profile.clt_expectation || sourced_profile.pj_expectation || sourced_profile.freelance_expectation,
        linkedin: build_linkedin_url(sourced_profile),
        github: sourced_profile.github,
        portfolio: sourced_profile.portfolio,
        self_introduction: sourced_profile.summary,
        curriculum_text: sourced_profile.curriculum_text
      )

      Rails.logger.info "✅ [ConvertToCandidateService] Candidate created successfully!"
      Rails.logger.info "   Candidate ID: #{candidate.id}"
      Rails.logger.info "   email present: #{candidate.email.present?}"
      Rails.logger.info "   mobile_phone present: #{candidate.mobile_phone.present?}"
      Rails.logger.info "   linkedin present: #{candidate.linkedin.present?}"
      Rails.logger.info "   current_company present: #{candidate.current_company.present?}"
      Rails.logger.info "   role_name present: #{candidate.role_name.present?}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      sourced_profile.update!(candidate: candidate)

      candidate
    end

    def find_existing_candidate(sourced_profile)
      return nil if sourced_profile.email.blank? && sourced_profile.cpf.blank? && sourced_profile.linkedin_slug.blank?

      conditions = []
      conditions << "email = :email" if sourced_profile.email.present?
      conditions << "cpf = :cpf" if sourced_profile.cpf.present?
      conditions << "linkedin ILIKE :linkedin" if sourced_profile.linkedin_slug.present?

      return nil if conditions.empty?

      Candidate.where(account_id: sourced_profile.account_id)
               .where(conditions.join(" OR "),
                      email: sourced_profile.email,
                      cpf: sourced_profile.cpf,
                      linkedin: "%#{sourced_profile.linkedin_slug}%")
               .first
    end

    def extract_email(sourced_profile)
      return sourced_profile.email if sourced_profile.email.present?
      return nil unless sourced_profile.emails.is_a?(Array) && sourced_profile.emails.any?

      sourced_profile.emails.first
    end

    def extract_phone(sourced_profile)
      return sourced_profile.phone if sourced_profile.phone.present?
      return nil unless sourced_profile.phones.is_a?(Array) && sourced_profile.phones.any?

      sourced_profile.phones.first
    end

    def build_linkedin_url(sourced_profile)
      return sourced_profile.linkedin_url if sourced_profile.linkedin_url.present?
      return sourced_profile.linkedin if sourced_profile.linkedin.present?

      linkedin_slug = sourced_profile.linkedin_slug || sourced_profile.external_id
      return nil if linkedin_slug.blank?

      "https://www.linkedin.com/in/#{linkedin_slug}"
    end

    def map_gender(gender)
      return nil if gender.blank?

      case gender.to_i
      when 0, 1 then 1
      when 2, 3 then 2
      else 6
      end
    end

    def sync_pending_applies(candidate)
      applies = Apply.where(candidate_id: candidate.id, external_id: nil)
      return if applies.empty?

      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      Rails.logger.info("🔄 [ConvertToCandidateService] Syncing #{applies.count} pending applies")
      Rails.logger.info("   Candidate: #{candidate.id} - #{candidate.name}")
      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

      applies.each do |apply|
        AtsSync::ProcessApplyWithEnrichmentJob.perform_in(2.seconds, apply.id, apply.account_id)
      end
    end

    def map_marital_status(status)
      return nil if status.blank?

      case status.to_i
      when 0, 1 then 1
      when 2, 3 then 2
      when 4, 5 then 3
      when 6 then 4
      else 7
      end
    end

    def create_skills(candidate, sourced_profile)
      skills_from_data = sourced_profile.skills_data || []
      skills_from_expertise = sourced_profile.expertise || []

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔧 [ConvertToCandidateService] CREATE SKILLS"
      Rails.logger.info "   Candidate ID: #{candidate.id}"
      Rails.logger.info "   SourcedProfile ID: #{sourced_profile.id}"
      Rails.logger.info "   skills_data: #{skills_from_data.size} items"
      Rails.logger.info "   expertise: #{skills_from_expertise.size} items"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      all_skill_names = []

      skills_from_data.each do |skill_data|
        skill_name = skill_data.is_a?(Hash) ? skill_data["skill"] : skill_data
        all_skill_names << skill_name if skill_name.present?
      end

      skills_from_expertise.each do |skill_name|
        all_skill_names << skill_name if skill_name.present?
      end

      Rails.logger.info "📊 Total unique skills to create: #{all_skill_names.uniq.size}"

      created_count = 0
      all_skill_names.uniq.each do |skill_name|
        next if skill_name.blank?

        skill = Skill.find_or_create_by!(
          name: skill_name.strip.downcase,
          account_id: sourced_profile.account_id
        )

        SkillRelationship.find_or_create_by!(
          skill: skill,
          reference: candidate,
          account_id: sourced_profile.account_id
        )

        created_count += 1
      rescue => e
        Rails.logger.warn("Failed to create skill '#{skill_name}': #{e.message}")
      end

      Rails.logger.info "✅ Created #{created_count} skill relationships"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def create_educations(candidate, sourced_profile)
      educations = sourced_profile.educations_data || sourced_profile.profile_data&.dig("educations") || []
      return if educations.empty?

      educations.each do |edu_data|
        next if edu_data.blank?

        Education.create!(
          candidate: candidate,
          account_id: sourced_profile.account_id,
          institution_name: edu_data["campus"],
          study_area_name: edu_data["major"],
          start_date: parse_date(edu_data["start_date"]),
          end_date: parse_date(edu_data["end_date"]),
          study_here: edu_data["end_date"].blank?
        )
      rescue => e
        Rails.logger.warn("Failed to create education: #{e.message}")
      end
    end

    def create_experiences(candidate, sourced_profile)
      experiences = sourced_profile.experiences_data || sourced_profile.profile_data&.dig("experiences") || []
      return if experiences.empty?

      experiences.each do |exp_data|
        next if exp_data["type"] != "company-experiences"

        company_roles = exp_data["company_roles"] || []
        company_info = exp_data["company_info"] || {}

        company_roles.each do |role|
          next if role.blank?

          Experience.create!(
            candidate: candidate,
            account_id: sourced_profile.account_id,
            company_name: role["company"] || company_info["name"],
            occupation_name: role["title"],
            start_date: parse_date(role["start_date"]),
            end_date: parse_date(role["end_date"]),
            work_here: role["is_current_experience"] || false,
            description: company_info["description"]
          )
        rescue => e
          Rails.logger.warn("Failed to create experience: #{e.message}")
        end
      end
    end

    def create_languages(candidate, sourced_profile)
      languages = sourced_profile.languages_data || sourced_profile.profile_data&.dig("languages") || []
      return if languages.empty?

      languages.each do |lang_data|
        next if lang_data.blank?

        lang_name = lang_data["name"] || lang_data["language"]
        next if lang_name.blank?

        language = Language.find_or_create_by!(name: lang_name) do |lang|
          lang.acronym = lang_name[0..2].upcase
          lang.name_ptbr = lang_name
        end

        LanguageRelationship.find_or_create_by!(
          language: language,
          reference: candidate,
          level: map_language_level(lang_data["level"])
        )
      rescue => e
        Rails.logger.warn("Failed to create language: #{e.message}")
      end
    end

    def parse_date(date_string)
      return nil if date_string.blank?

      Date.parse(date_string)
    rescue ArgumentError
      nil
    end

    def map_language_level(level)
      return "intermediário" if level.blank?

      case level.to_s.downcase
      when "basic", "beginner", "elementary", "a1", "a2" then "básico"
      when "intermediate", "intermediary", "b1", "b2" then "intermediário"
      when "advanced", "c1" then "avançado"
      when "fluent", "c2" then "fluente"
      when "native" then "nativo"
      else "intermediário"
      end
    end

    def discover_email_if_needed(sourced_profile)
      return if extract_email(sourced_profile).present?
      return unless should_discover_email?(sourced_profile)

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "📧 [ConvertToCandidateService] DISCOVERING EMAIL VIA PEARCH"
      Rails.logger.info "   SourcedProfile ID: #{sourced_profile.id}"
      Rails.logger.info "   Account has ATS: #{sourced_profile.account.ats_provider}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      user = sourced_profile.account.users.find_by(is_admin: true) || sourced_profile.account.users.first
      return unless user

      enrichment_service = Pearch::ContactEnrichmentService.new(
        sourced_profile: sourced_profile,
        user: user,
        enrich_emails: true,
        enrich_phones: false,
        require_phones_or_emails: false
      )

      result = enrichment_service.enrich!

      if result[:success] && result[:emails_found]
        sourced_profile.reload
        Rails.logger.info "✅ Email discovered: #{sourced_profile.emails&.first}"
      else
        Rails.logger.warn "⚠️  Email discovery failed: #{result[:error]}"
      end
    rescue StandardError => e
      Rails.logger.error "❌ Email discovery error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
    end

    def should_discover_email?(sourced_profile)
      return false unless sourced_profile.account.present?
      return false unless sourced_profile.account.ats_provider.present?
      return false unless sourced_profile.external_id.present?

      true
    end
  end
end
