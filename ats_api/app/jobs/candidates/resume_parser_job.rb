# frozen_string_literal: true

module Candidates
  class ResumeParserJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 3

    def perform(args)
      @args = args

      Rails.logger.info "[ResumeParserJob] Starting using #{ai_provider}"

      if account_id.present?
        account = Account.find_by(id: account_id)
        return unless account

        Apartment::Tenant.switch(account.tenant) { execute }
      else
        execute
      end
    rescue => e
      handle_error(e)
    end

    def execute
      candidate = prepare_candidate
      return log_no_text_error if candidate.curriculum_text.blank?

      process_resume(candidate)
    end

    private

    def prepare_candidate
      return process_existing_candidate if candidate_id.present?

      create_new_candidate_with_text
    end

    def process_existing_candidate
      candidate = Candidate.find(candidate_id)
      extract_text_from_pdf(candidate)
      candidate.reload
    end

    def create_new_candidate_with_text
      candidate = create_initial_candidate
      candidate.update(curriculum_text: resume_text)
      candidate
    end

    def process_resume(candidate)
      result = parse_resume_text(candidate.curriculum_text)

      if result[:success]
        candidate.update(data_raw: result[:data])
        update_candidate_with_data(candidate, result[:data])
        log_success(candidate.id)
      else
        log_parser_error(result[:error])
      end

      { success: true, candidate_id: candidate.id }
    rescue => e
      log_error("Resume processing failed: #{e.message}")
      { success: false, error: e.message }
    end

    def parse_resume_text(text)
      service = Candidates::ResumeParserService.new(text, additional_data, ai_provider: ai_provider)
      service.call
    end

    def candidate_id
      @args["candidate_id"] || @args[:candidate_id]
    end

    def account_id
      @args["account_id"] || @args[:account_id]
    end

    def resume_text
      @args["resume_text"] || @args[:resume_text]
    end

    def additional_data
      data = @args["additional_data"] || @args[:additional_data] || {}
      data.is_a?(Hash) ? data.with_indifferent_access : {}
    end

    def ai_provider
      (@args["ai_provider"] || @args[:ai_provider] || :gemini).to_sym
    end

    def create_initial_candidate
      Candidate.create!(
        account_id: account_id,
        name: additional_data[:name] || "Candidato Importado",
        email: additional_data[:email],
        mobile_phone: additional_data[:phone]
      )
    end

    def extract_text_from_pdf(candidate)
      return unless candidate.curriculum_pdf.attached?

      io = StringIO.new(candidate.curriculum_pdf.download)
      text = Yomu.new(io).text
      candidate.update(curriculum_text: text) if text.present?
    rescue => e
      log_error("PDF extraction failed: #{e.message}")
    end

    def update_candidate_with_data(candidate, data)
      candidate.update(candidate_attributes(candidate, data))

      create_relationships(candidate, data)
    end

    def candidate_attributes(candidate, data)
      {
        name: data[:name] || candidate.name,
        email: data[:email] || candidate.email,
        mobile_phone: data[:mobile_phone] || data[:phone] || candidate.mobile_phone,
        linkedin: data[:linkedin],
        github: data[:github],
        portfolio: data[:portfolio],
        current_company: data[:current_company],
        role_name: data[:role_name],
        self_introduction: data[:self_introduction] || data[:summary],
        city: data[:city],
        state: data[:state],
        country: data[:country],
        data_raw: build_data_raw(data)
      }
    end

    def build_data_raw(data)
      return data if data[:data_raw].present?

      {
        basic_info: {
          fullname: data[:name],
          email: data[:email],
          mobile_phone: data[:mobile_phone],
          linkedin: data[:linkedin],
          github: data[:github],
          portfolio: data[:portfolio],
          current_company: data[:current_company],
          role_name: data[:role_name],
          about: data[:self_introduction] || data[:summary],
          location: { city: data[:city], state: data[:state], country: data[:country] }
        },
        education: data[:educations] || [],
        experience: data[:experiences] || [],
        languages: data[:languages] || []
      }
    end

    def create_relationships(candidate, data)
      create_skills(candidate, data[:skills]) if data[:skills].present?
      create_languages(candidate, data[:languages]) if data[:languages].present?
      create_experiences(candidate, data[:experiences]) if data[:experiences].present?
      create_educations(candidate, data[:educations]) if data[:educations].present?
    end

    def create_skills(candidate, skills)
      skills.each { |skill_name| create_skill_relationship(candidate, skill_name) }
    rescue => e
      Rails.logger.error "[ResumeParserJob] Failed to create skills: #{e.message}"
    end

    def create_skill_relationship(candidate, skill_name)
      return if skill_name.blank?
      return if skill_already_exists?(candidate, skill_name)

      skill = find_or_create_skill(candidate, skill_name)
      candidate.skill_relationships.create(skill_id: skill.id)
    end

    def skill_already_exists?(candidate, skill_name)
      skill = Skill.find_by(name: skill_name.strip, account_id: candidate.account_id)
      return false unless skill

      candidate.skill_relationships.exists?(skill_id: skill.id)
    end

    def find_or_create_skill(candidate, skill_name)
      Skill.find_or_create_by(name: skill_name.strip, account_id: candidate.account_id)
    end

    def create_languages(candidate, languages)
      languages.each { |lang_data| create_language_relationship(candidate, lang_data) }
    rescue => e
      Rails.logger.error "[ResumeParserJob] Failed to create languages: #{e.message}"
    end

    def create_language_relationship(candidate, lang_data)
      language_name = lang_data[:language] || lang_data[:name]
      return if language_name.blank?

      language = find_or_create_language(candidate, language_name)
      return unless language
      return if language_already_exists?(candidate, language.id)

      level = lang_data[:level] || lang_data[:proficiency]
      candidate.language_relationships.create(
        language_id: language.id,
        level: map_level(level),
        reference_type: "Candidate",
        reference_id: candidate.id
      )
    end

    def language_already_exists?(candidate, language_id)
      candidate.language_relationships.exists?(language_id: language_id)
    end

    def find_or_create_language(candidate, language_name)
      processor = Candidates::LinkedinDataProcessor.new(candidate, {})
      processor.send(:find_or_create_language, language_name)
    end

    def create_experiences(candidate, experiences)
      experiences.each { |exp_data| create_experience(candidate, exp_data) }
    rescue => e
      Rails.logger.error "[ResumeParserJob] Failed to create experiences: #{e.message}"
    end

    def create_experience(candidate, exp_data)
      return if exp_data[:company].blank? || exp_data[:position].blank?

      candidate.experiences.create(
        company: exp_data[:company],
        position: exp_data[:position],
        start_date: parse_date(exp_data[:start_date]),
        end_date: parse_date(exp_data[:end_date]),
        description: exp_data[:description],
        is_current: exp_data[:is_current] || false
      )
    end

    def create_educations(candidate, educations)
      educations.each { |edu_data| create_education(candidate, edu_data) }
    rescue => e
      Rails.logger.error "[ResumeParserJob] Failed to create educations: #{e.message}"
    end

    def create_education(candidate, edu_data)
      return if edu_data[:institution].blank? || edu_data[:degree].blank?

      candidate.educations.create(
        institution: edu_data[:institution],
        degree: edu_data[:degree],
        field_of_study: edu_data[:field_of_study],
        start_date: parse_date(edu_data[:start_date]),
        end_date: parse_date(edu_data[:end_date])
      )
    end

    def parse_date(date_str)
      return nil if date_str.blank?
      return date_str if date_str.is_a?(Date) || date_str.is_a?(Time)

      Date.parse(date_str.to_s) rescue nil
    end

    def map_level(level)
      return "intermediário" if level.blank?

      level_lower = level.downcase

      return "nativo" if native_level?(level_lower)
      return "fluente" if fluent_level?(level_lower)
      return "avançado" if advanced_level?(level_lower)
      return "intermediário" if intermediate_level?(level_lower)
      return "básico" if basic_level?(level_lower)

      "intermediário"
    end

    def native_level?(level)
      level.include?("nativ") || level.include?("mother")
    end

    def fluent_level?(level)
      level.include?("fluent") || level.include?("proficient")
    end

    def advanced_level?(level)
      level.include?("advanced") || level.include?("avançado")
    end

    def intermediate_level?(level)
      level.include?("intermediate") || level.include?("intermediário")
    end

    def basic_level?(level)
      level.include?("basic") || level.include?("básico") || level.include?("elementary")
    end

    def log_error(message)
      Rails.logger.error "[ResumeParserJob] #{message}"
    end

    def log_no_text_error
      Rails.logger.error("[ResumeParserJob] No text extracted")
    end

    def log_parser_error(error)
      Rails.logger.error "[ResumeParserJob] Parser failed: #{error}"
      { success: false, error: error }
    end

    def log_success(candidate_id)
      Rails.logger.info "[ResumeParserJob] Candidate updated: #{candidate_id}"
    end

    def handle_error(error)
      Rails.logger.error "[ResumeParserJob] Error: #{error.message}"
      Rails.logger.error error.backtrace.first(5).join("\n")

      raise error if sidekiq_options_hash["retry"] != false
    end
  end
end
