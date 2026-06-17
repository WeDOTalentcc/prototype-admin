# frozen_string_literal: true

module Candidates
  class LinkedinDataProcessor
    attr_reader :candidate, :linkedin_data

    def initialize(candidate, linkedin_data)
      @candidate = candidate
      @linkedin_data = linkedin_data
    end

    def process_all
      stats = {
        basic_fields: update_basic_fields,
        avatar: process_avatar,
        skills: process_skills,
        languages: process_languages,
        experiences: process_experiences,
        educations: process_educations,
        curriculum_text: generate_curriculum_text
      }

      Rails.logger.info "[LinkedinDataProcessor] Processed data for candidate ##{candidate.id}: #{stats.inspect}"
      stats
    end

    private

    def basic_info
      @basic_info ||= linkedin_data[:basic_info] || linkedin_data["basic_info"] || {}
    end

    def update_basic_fields
      updates = {}

      fullname = basic_info[:fullname] || basic_info["fullname"]
      if fullname.present?
        updates[:name] = fullname
      end

      email = basic_info[:email] || basic_info["email"]
      if email.present? && candidate.email.blank?
        updates[:email] = email
      end

      profile_url = basic_info[:profile_url] || basic_info["profile_url"]
      if profile_url.present?
        updates[:linkedin] = profile_url
      end

      headline = basic_info[:headline] || basic_info["headline"]
      if headline.present? && candidate.role_name.blank?
        updates[:role_name] = headline
      end

      about = basic_info[:about] || basic_info["about"]
      if about.present? && candidate.self_introduction.blank?
        updates[:self_introduction] = about
      end

      location = parse_location
      updates.merge!(location) if location.any?

      return { updated: false } if updates.empty?

      candidate.update!(updates)
      { updated: true, fields: updates.keys }
    end

    def parse_location
      updates = {}
      location = basic_info[:location] || basic_info["location"]
      return updates unless location.present?

      location_full = location[:full] || location["full"]
      return updates unless location_full.present?

      parts = location_full.split(",").map(&:strip)

      updates[:city] = parts[0] if parts[0].present? && candidate.city.blank?
      updates[:state] = parts[1] if parts[1].present? && candidate.state.blank?
      updates[:country] = parts[2] if parts[2].present? && candidate.country.blank?

      updates
    end

    def process_avatar
      profile_picture_url = basic_info[:profile_picture_url] || basic_info["profile_picture_url"]
      return { downloaded: false, reason: "URL não encontrada" } if profile_picture_url.blank?
      return { downloaded: false, reason: "Avatar já existe" } if candidate.avatar.attached?

      downloader = Candidates::AvatarDownloaderService.new(candidate, profile_picture_url)
      result = downloader.call

      if result[:success]
        { downloaded: true, filename: result[:filename] }
      else
        { downloaded: false, error: result[:error] }
      end
    end

    def process_languages
      languages_list = linkedin_data[:languages] || linkedin_data["languages"]
      return { created: 0 } unless languages_list.present? && languages_list.is_a?(Array)

      created_count = 0

      languages_list.each do |lang_data|
        next if lang_data.blank?

        language_name = lang_data[:language] || lang_data["language"]
        proficiency = lang_data[:proficiency] || lang_data["proficiency"]

        next if language_name.blank?

        language = find_or_create_language(language_name)
        next unless language

        unless language_already_linked?(language)
          level = map_proficiency_to_level(proficiency)
          create_language_relationship(language, level)
          created_count += 1
        end
      end

      { created: created_count, total: languages_list.size }
    end

    def find_or_create_language(name)
      normalized_name = normalize_language_name(name.strip)

      language = Language.where("LOWER(name) = ? OR LOWER(name_ptbr) = ?",
                                normalized_name.downcase,
                                normalized_name.downcase).first

      return language if language

      acronym = generate_language_acronym(normalized_name)
      name_ptbr = translate_language_to_portuguese(normalized_name)

      Language.create!(
        name: normalized_name,
        acronym: acronym,
        name_ptbr: name_ptbr
      )
    rescue ActiveRecord::RecordInvalid => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create language #{name}: #{e.message}"
      Language.where("LOWER(name) = ?", normalized_name.downcase).first
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Unexpected error creating language #{name}: #{e.message}"
      nil
    end

    def normalize_language_name(name)
      name_map = {
        "english" => "English",
        "portuguese" => "Portuguese",
        "spanish" => "Spanish",
        "french" => "French",
        "german" => "German",
        "italian" => "Italian",
        "chinese" => "Chinese",
        "japanese" => "Japanese",
        "korean" => "Korean",
        "russian" => "Russian",
        "arabic" => "Arabic",
        "dutch" => "Dutch",
        "swedish" => "Swedish",
        "polish" => "Polish",
        "turkish" => "Turkish",
        "hindi" => "Hindi",
        "mandarin" => "Chinese"
      }

      name_map[name.downcase] || name.capitalize
    end

    def generate_language_acronym(name)
      acronym_map = {
        "English" => "EN",
        "Portuguese" => "PT",
        "Spanish" => "ES",
        "French" => "FR",
        "German" => "DE",
        "Italian" => "IT",
        "Chinese" => "ZH",
        "Japanese" => "JA",
        "Korean" => "KO",
        "Russian" => "RU",
        "Arabic" => "AR",
        "Dutch" => "NL",
        "Swedish" => "SV",
        "Polish" => "PL",
        "Turkish" => "TR",
        "Hindi" => "HI"
      }

      acronym_map[name] || name[0..1].upcase
    end

    def translate_language_to_portuguese(name)
      translation_map = {
        "English" => "Inglês",
        "Portuguese" => "Português",
        "Spanish" => "Espanhol",
        "French" => "Francês",
        "German" => "Alemão",
        "Italian" => "Italiano",
        "Chinese" => "Chinês",
        "Japanese" => "Japonês",
        "Korean" => "Coreano",
        "Russian" => "Russo",
        "Arabic" => "Árabe",
        "Dutch" => "Holandês",
        "Swedish" => "Sueco",
        "Polish" => "Polonês",
        "Turkish" => "Turco",
        "Hindi" => "Hindi"
      }

      translation_map[name] || name
    end

    def map_proficiency_to_level(proficiency)
      return nil if proficiency.blank?

      proficiency_lower = proficiency.downcase

      return "nativo" if proficiency_lower.include?("native") || proficiency_lower.include?("bilingual")
      return "fluente" if proficiency_lower.include?("full professional") || proficiency_lower.include?("fluent")
      return "avançado" if proficiency_lower.include?("professional working")
      return "intermediário" if proficiency_lower.include?("limited working") || proficiency_lower.include?("intermediate")
      return "básico" if proficiency_lower.include?("elementary") || proficiency_lower.include?("basic")

      "intermediário"
    end

    def language_already_linked?(language)
      candidate.language_relationships.exists?(language_id: language.id)
    end

    def create_language_relationship(language, level)
      candidate.language_relationships.create!(
        language_id: language.id,
        level: level,
        reference_type: "Candidate",
        reference_id: candidate.id
      )
    end

    def process_skills
      skills_list = basic_info[:top_skills] || basic_info["top_skills"]
      return { created: 0 } unless skills_list.present? && skills_list.is_a?(Array)

      created_count = 0

      skills_list.each do |skill_name|
        next if skill_name.blank?

        skill = find_or_create_skill(skill_name)
        next unless skill

        unless skill_already_linked?(skill)
          create_skill_relationship(skill)
          created_count += 1
        end
      end

      { created: created_count, total: skills_list.size }
    end

    def find_or_create_skill(name)
      Skill.find_or_create_by(name: name.strip, account_id: candidate.account_id)
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create skill #{name}: #{e.message}"
      nil
    end

    def skill_already_linked?(skill)
      candidate.skill_relationships.exists?(skill_id: skill.id)
    end

    def create_skill_relationship(skill)
      candidate.skill_relationships.create!(
        skill_id: skill.id,
        account_id: candidate.account_id
      )
    end

    def process_experiences
      experiences_list = linkedin_data[:experience] || linkedin_data["experience"]
      return { created: 0 } unless experiences_list.present? && experiences_list.is_a?(Array)

      created_count = 0

      experiences_list.each do |exp_data|
        next if exp_data.blank?

        experience = create_experience(exp_data)
        created_count += 1 if experience
      end

      { created: created_count, total: experiences_list.size }
    end

    def create_experience(exp_data)
      company_name = exp_data[:company] || exp_data["company"]
      title = exp_data[:title] || exp_data["title"]

      return nil if company_name.blank? || title.blank?

      company = find_or_create_company(company_name)
      return nil unless company

      occupation = find_or_create_occupation(title)
      return nil unless occupation

      is_current = exp_data[:is_current] || exp_data["is_current"]
      description = exp_data[:description] || exp_data["description"]
      start_date = parse_linkedin_date(exp_data[:start_date] || exp_data["start_date"])

      return nil unless start_date

      end_date = parse_linkedin_date(exp_data[:end_date] || exp_data["end_date"]) unless is_current

      candidate.experiences.create!(
        company_id: company.id,
        occupation_id: occupation.id,
        work_here: is_current || false,
        description: description,
        start_date: start_date,
        end_date: end_date,
        account_id: candidate.account_id,
        user_id: candidate.account.users.first&.id,
        candidate_id: candidate.id,
        is_deleted: false
      )
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create experience: #{e.message}"
      Rails.logger.error e.backtrace.first(3).join("\n")
      nil
    end

    def process_educations
      educations_list = linkedin_data[:education] || linkedin_data["education"]
      return { created: 0 } unless educations_list.present? && educations_list.is_a?(Array)

      created_count = 0

      educations_list.each do |edu_data|
        next if edu_data.blank?

        education = create_education(edu_data)
        created_count += 1 if education
      end

      { created: created_count, total: educations_list.size }
    end

    def create_education(edu_data)
      school_name = edu_data[:school] || edu_data["school"]
      return nil if school_name.blank?

      institution = find_or_create_institution(school_name)
      return nil unless institution

      field_of_study = edu_data[:field_of_study] || edu_data["field_of_study"]
      study_area = find_or_create_study_area(field_of_study) if field_of_study.present?

      degree_name = edu_data[:degree] || edu_data["degree"] || edu_data[:degree_name] || edu_data["degree_name"]
      formation_type = map_formation_type(degree_name)

      start_date = parse_linkedin_date(edu_data[:start_date] || edu_data["start_date"])
      end_date = parse_linkedin_date(edu_data[:end_date] || edu_data["end_date"])
      study_here = end_date.nil? && start_date.present?

      candidate.educations.create!(
        institution_id: institution.id,
        study_area_id: study_area&.id,
        formation_type: formation_type,
        study_here: study_here,
        start_date: start_date,
        end_date: end_date,
        account_id: candidate.account_id
      )
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create education: #{e.message}"
      Rails.logger.error e.backtrace.first(3).join("\n")
      nil
    end

    def find_or_create_company(name)
      normalized_name = name.strip.downcase

      company = Company.where(name: normalized_name, account_id: candidate.account_id, is_deleted: false).first
      return company if company

      company = Company.create!(
        name: normalized_name,
        account_id: candidate.account_id
      )

      company
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create company #{name}: #{e.message}"
      nil
    end

    def find_or_create_occupation(title)
      normalized_title = title.strip.downcase

      occupation = Occupation.where(name: normalized_title, account_id: candidate.account_id).first
      return occupation if occupation

      occupation = Occupation.create!(
        name: normalized_title,
        account_id: candidate.account_id
      )

      occupation
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create occupation #{title}: #{e.message}"
      nil
    end

    def find_or_create_institution(name)
      Institution.find_or_create_by(name: name.strip, account_id: candidate.account_id)
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create institution #{name}: #{e.message}"
      nil
    end

    def find_or_create_study_area(field)
      return nil if field.blank?
      StudyArea.find_or_create_by(name: field.strip, account_id: candidate.account_id)
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to create study area #{field}: #{e.message}"
      nil
    end

    def map_formation_type(degree_name)
      return 8 if degree_name.blank?

      degree_lower = degree_name.downcase

      return 1 if degree_lower.include?("fundamental") || degree_lower.include?("elementary")
      return 2 if degree_lower.include?("médio") || degree_lower.include?("high school")
      return 3 if degree_lower.include?("técnico") || degree_lower.include?("technical")
      return 4 if degree_lower.include?("tecnólogo") || degree_lower.include?("technology")
      return 5 if degree_lower.include?("bacharelado") || degree_lower.include?("bachelor")
      return 6 if degree_lower.include?("licenciatura") || degree_lower.include?("teaching")
      return 7 if degree_lower.include?("pós") || degree_lower.include?("especialização") || degree_lower.include?("mba") || degree_lower.include?("master") || degree_lower.include?("phd") || degree_lower.include?("doutorado")

      8
    end

    def parse_linkedin_date(date_data)
      return nil if date_data.blank?

      if date_data.is_a?(Hash)
        year = date_data[:year] || date_data["year"]
        month = date_data[:month] || date_data["month"] || 1
        day = date_data[:day] || date_data["day"] || 1

        return nil unless year

        month = parse_month_value(month)

        Date.new(year.to_i, month.to_i, day.to_i)
      elsif date_data.is_a?(String)
        Date.parse(date_data)
      end
    rescue ArgumentError, TypeError
      nil
    end

    def parse_month_value(month)
      return 1 if month.blank?
      return month if month.is_a?(Integer)
      return month.to_i if month.to_s.match?(/^\d+$/)

      month_map = {
        "jan" => 1, "january" => 1, "janeiro" => 1,
        "feb" => 2, "february" => 2, "fevereiro" => 2,
        "mar" => 3, "march" => 3, "março" => 3,
        "apr" => 4, "april" => 4, "abril" => 4,
        "may" => 5, "maio" => 5,
        "jun" => 6, "june" => 6, "junho" => 6,
        "jul" => 7, "july" => 7, "julho" => 7,
        "aug" => 8, "august" => 8, "agosto" => 8,
        "sep" => 9, "september" => 9, "setembro" => 9,
        "oct" => 10, "october" => 10, "outubro" => 10,
        "nov" => 11, "november" => 11, "novembro" => 11,
        "dec" => 12, "december" => 12, "dezembro" => 12
      }

      month_map[month.to_s.downcase] || 1
    end

    def generate_curriculum_text
      return { generated: false, error: "Candidate not persisted" } unless candidate.persisted?

      curriculum = CurriculumTextGenerator.new(candidate).generate

      if curriculum.present?
        candidate.update!(curriculum_text: curriculum)
        { generated: true, length: curriculum.length }
      else
        { generated: false, error: "Empty curriculum" }
      end
    rescue => e
      Rails.logger.error "[LinkedinDataProcessor] Failed to generate curriculum text: #{e.message}"
      Rails.logger.error e.backtrace.first(3).join("\n")
      { generated: false, error: e.message }
    end
  end
end
