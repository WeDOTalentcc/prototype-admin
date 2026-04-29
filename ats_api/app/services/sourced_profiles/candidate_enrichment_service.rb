module SourcedProfiles
  class CandidateEnrichmentService
    def initialize(sourced_profile, candidate)
      @profile = sourced_profile
      @candidate = candidate
    end

    def self.call(sourced_profile, candidate)
      new(sourced_profile, candidate).call
    end

    def call
      return @profile unless @candidate.present?

      @profile.assign_attributes(enriched_attributes)
      @profile
    end

    private

    def enriched_attributes
      {
        name: full_name,
        first_name: @candidate.name&.split&.first,
        last_name: @candidate.name&.split&.last,
        email: @candidate.email.presence || @profile.email,
        phone: primary_phone,
        cpf: @candidate.cpf.presence || @profile.cpf,
        date_birth: @candidate.date_birth || @profile.date_birth,
        title: current_position_title,
        summary: @candidate.self_introduction.presence || @candidate.comments.presence || @profile.summary,
        picture_url: @candidate.avatar_public_url.presence || @profile.picture_url,
        gender: map_gender,
        marital_status: map_marital_status,
        estimated_age: calculate_age,
        location: full_location,
        city: @candidate.city.presence || @profile.city,
        state: @candidate.state.presence || @profile.state,
        country: @candidate.country.presence || @profile.country,
        address: @candidate.street,
        zip_code: @candidate.zip,
        current_company: current_company_name,
        current_title: current_position_title,
        role_name: current_position_title,
        position_level: infer_seniority,
        total_experience_years: calculate_total_experience,
        currency: "BRL",
        clt_expectation: @candidate.desired_salary,
        expertise: extract_skills,
        languages_data: build_languages_data,
        skills_data: build_skills_data,
        behavioral_skills_list: SourcedProfile.behavioral_skills_list_from_candidate(@candidate),
        has_emails: @candidate.email.present?,
        has_phone_numbers: (primary_phone || @candidate.mobile_phone).present?,
        profile_data: build_profile_data,
        experiences_data: build_experiences_data,
        educations_data: build_educations_data,
        linkedin: @candidate.linkedin,
        github: @candidate.github,
        portfolio: @candidate.portfolio,
        secondary_email: @candidate.secondary_email,
        mobile_phone: @candidate.mobile_phone,
        secondary_phone: @candidate.secondary_phone,
        street: @candidate.street,
        number: @candidate.number,
        district: @candidate.district,
        complement: @candidate.complement,
        zip: @candidate.zip,
        nationality: @candidate.nationality,
        self_introduction: @candidate.self_introduction,
        curriculum_text: build_curriculum_text,
        current_salary: @candidate.current_salary,
        desired_salary: @candidate.desired_salary,
        interests: @candidate.interests,
        comments: @candidate.comments,
        curriculum_pdf_url: @candidate.curriculum_pdf_url,
        profile_updated_at: Time.current
      }
    end

    def full_name
      @candidate.name.presence || @profile.name
    end

    def primary_phone
      @candidate.phone.presence || @candidate.mobile_phone.presence || @profile.phone
    end

    def current_position_title
      current_exp = @candidate.experiences.where(work_here: true).order(start_date: :desc).first
      current_exp&.occupation&.name || @profile.title
    end

    def current_company_name
      current_exp = @candidate.experiences.where(work_here: true).order(start_date: :desc).first
      current_exp&.company&.name || @profile.current_company
    end

    def map_gender
      return @profile.gender unless @candidate.gender.present?

      case @candidate.gender
      when 1, 3 then "male"
      when 2, 4 then "female"
      else nil
      end
    end

    def map_marital_status
      return @profile.marital_status unless @candidate.marital_status.present?

      case @candidate.marital_status
      when 1 then "single"
      when 2, 5 then "married"
      when 3 then "divorced"
      when 4 then "widowed"
      else nil
      end
    end

    def calculate_age
      return @profile.estimated_age unless @candidate.date_birth.present?

      ((Time.current - @candidate.date_birth.to_time) / 1.year.seconds).floor
    end

    def full_location
      parts = [
        @candidate.city,
        @candidate.state,
        @candidate.country
      ].compact

      parts.any? ? parts.join(", ") : @profile.location
    end

    def infer_seniority
      total_years = calculate_total_experience
      return nil unless total_years

      case total_years
      when 0..2 then "junior"
      when 3..5 then "mid"
      when 6..9 then "senior"
      else "lead"
      end
    end

    def calculate_total_experience
      return nil if @candidate.experiences.empty?

      total_months = @candidate.experiences.sum do |exp|
        start_date = exp.start_date
        end_date = exp.end_date || Date.current

        ((end_date.year - start_date.year) * 12 + (end_date.month - start_date.month))
      end

      (total_months / 12.0).round(1)
    end

    def extract_skills
      @candidate.skills.pluck(:name).map(&:downcase).uniq
    end

    def build_languages_data
      @candidate.language_relationships.includes(:language).map do |rel|
        {
          language: rel.language.name,
          proficiency: map_proficiency(rel.level),
          proficiency_code: map_cefr_level(rel.level)
        }
      end
    end

    def build_skills_data
      @candidate.skills.map do |skill|
        {
          name: skill.name,
          category: "technical",
          proficiency: "intermediate"
        }
      end
    end

    def build_profile_data
      {
        docid: @profile.external_id,
        title: current_position_title,
        summary: @candidate.self_introduction || @candidate.comments,
        location: full_location,
        first_name: @candidate.name&.split&.first,
        last_name: @candidate.name&.split&.last,
        middle_name: nil,
        has_emails: @candidate.email.present?,
        has_phone_numbers: primary_phone.present?,
        picture_url: @candidate.avatar_public_url,
        updated_date: @candidate.updated_at.to_date.to_s,
        estimated_age: calculate_age,
        total_experience_years: calculate_total_experience,
        is_decision_maker: false,
        is_top_universities: has_top_university?,
        expertise: extract_skills,
        experiences: build_experiences_data,
        educations: build_educations_data
      }
    end

    def build_experiences_data
      @candidate.experiences.includes(:company, :occupation, :city).order(start_date: :desc).map do |exp|
        {
          type: "company-experiences",
          company_info: {
            name: exp.company&.name,
            type: "company-info",
            domain: nil
          },
          company_roles: [ {
            title: exp.occupation&.name,
            company: exp.company&.name,
            location: [ exp.city&.name, exp.city&.state&.name ].compact.join(", "),
            start_date: exp.start_date.to_s,
            end_date: exp.end_date&.to_s,
            duration_years: calculate_duration_years(exp.start_date, exp.end_date),
            experience_summary: exp.description,
            is_current_experience: exp.work_here,
            contract_type: exp.contract_type
          } ]
        }
      end
    end

    def build_educations_data
      @candidate.educations.order(start_date: :desc).map do |edu|
        {
          institution: {
            name: edu.institution,
            type: infer_institution_type(edu.degree)
          },
          degree: {
            level: map_education_level(edu.degree),
            field: edu.course,
            start_date: edu.start_date&.year&.to_s,
            end_date: edu.end_date&.year&.to_s,
            status: edu.studying ? "in_progress" : "completed"
          }
        }
      end
    end

    def calculate_duration_years(start_date, end_date)
      return nil unless start_date

      end_date ||= Date.current
      months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
      (months / 12.0).round(1)
    end

    def has_top_university?
      top_universities = [
        "usp", "unicamp", "ita", "ufrj", "ufmg", "mit", "stanford",
        "harvard", "oxford", "cambridge"
      ]

      @candidate.educations.any? do |edu|
        institution = edu.institution.to_s.downcase
        top_universities.any? { |top| institution.include?(top) }
      end
    end

    def infer_institution_type(degree)
      return "university" unless degree

      case degree.downcase
      when /técnico|technical/ then "technical"
      when /bootcamp/ then "bootcamp"
      when /online|coursera|udemy/ then "online_platform"
      else "university"
      end
    end

    def map_education_level(degree)
      return nil unless degree

      case degree.downcase
      when /médio|high school/ then "high_school"
      when /técnico|technical/ then "technical"
      when /graduação|bachelor|bacharelado/ then "bachelor"
      when /pós|especialização|postgraduate/ then "postgraduate"
      when /mba/ then "mba"
      when /mestrado|master/ then "master"
      when /doutorado|phd/ then "phd"
      else "bachelor"
      end
    end

    def map_proficiency(level)
      return "intermediate" unless level

      case level.downcase
      when /básico|basic|a1|a2/ then "basic"
      when /intermediário|intermediate|b1|b2/ then "intermediate"
      when /avançado|advanced|c1/ then "advanced"
      when /fluente|fluent|nativo|native|c2/ then "fluent"
      else "intermediate"
      end
    end

    def map_cefr_level(level)
      return "B1" unless level

      case level.downcase
      when /básico|basic/ then "A2"
      when /intermediário|intermediate/ then "B1"
      when /avançado|advanced/ then "C1"
      when /fluente|fluent|nativo|native/ then "C2"
      else "B1"
      end
    end

    def build_curriculum_text
      return @candidate.curriculum_text if @candidate.curriculum_text.present? && @candidate.curriculum_text.length > 500
      extract_curriculum_text
    end

    def extract_curriculum_text
      sections = []

      # Header
      header_parts = [ @candidate.name, current_position_title ].compact
      sections << header_parts.join("\n") if header_parts.any?

      # Contact
      contact_parts = []
      contact_parts << "Email: #{@candidate.email}" if @candidate.email.present?
      contact_parts << "Telefone: #{primary_phone}" if primary_phone.present?
      contact_parts << "Localização: #{full_location}" if full_location.present?
      contact_parts << "LinkedIn: #{@candidate.linkedin}" if @candidate.linkedin.present?
      sections << contact_parts.join("\n") if contact_parts.any?

      # Summary
      if @candidate.self_introduction.present?
        sections << "SOBRE\n#{@candidate.self_introduction}"
      end

      # Experiences
      experiences = @candidate.experiences.order(start_date: :desc)
      if experiences.any?
        exp_text = experiences.map do |exp|
          parts = []
          parts << exp.occupation&.name || "Cargo não especificado"
          parts << exp.company&.name if exp.company&.name.present?

          dates = []
          dates << exp.start_date.strftime("%m/%Y") if exp.start_date
          dates << (exp.work_here ? "Atual" : exp.end_date&.strftime("%m/%Y"))
          parts << "(#{dates.compact.join(' - ')})" if dates.any?

          result = parts.join(" - ")
          result += "\n#{exp.description}" if exp.description.present?
          result
        end.join("\n\n")

        sections << "EXPERIÊNCIA PROFISSIONAL\n#{exp_text}"
      end

      # Education
      educations = @candidate.educations.order(start_date: :desc)
      if educations.any?
        edu_text = educations.map do |edu|
          parts = []
          parts << "#{edu.degree} em #{edu.course}" if edu.course.present?
          parts << edu.institution if edu.institution.present?
          parts << edu.start_date&.year&.to_s if edu.start_date
          parts.compact.join(" - ")
        end.join("\n")

        sections << "FORMAÇÃO ACADÊMICA\n#{edu_text}"
      end

      # Skills
      skills = @candidate.skills.pluck(:name)
      if skills.any?
        sections << "HABILIDADES\n#{skills.join(", ")}"
      end

      # Languages
      languages = @candidate.language_relationships.includes(:language).map { |cl| "#{cl.language&.name} (#{cl.level})" }
      if languages.any?
        sections << "IDIOMAS\n#{languages.join(", ")}"
      end

      # Additional info
      if @candidate.comments.present?
        sections << "OBSERVAÇÕES\n#{@candidate.comments}"
      end

      sections.compact.join("\n\n")
    end
  end
end
