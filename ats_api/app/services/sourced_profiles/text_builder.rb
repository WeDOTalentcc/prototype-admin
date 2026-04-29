module SourcedProfiles
  class TextBuilder
    def self.call(sourced_profile)
      new(sourced_profile).call
    end

    def initialize(sourced_profile)
      @profile = sourced_profile
    end

    def call
      parts = build_parts
      return nil if parts.empty?

      parts.compact.map(&:to_s).map(&:strip).reject(&:empty?).join("\n\n")
    end

    private

    attr_reader :profile

    def build_parts
      [
        identity,
        headline,
        summary_text,
        curriculum_text,
        location_info,
        work_preferences,
        salary_info,
        skills_list,
        experiences_text,
        educations_text,
        languages_list,
        links_info
      ]
    end

    def identity
      profile.full_name.presence || profile.name
    end

    def headline
      [ profile.title, profile.role_name, profile.position_level ].compact.join(" · ").presence
    end

    def summary_text
      profile.summary.presence || profile.self_introduction.presence
    end

    def curriculum_text
      profile.curriculum_text.presence
    end

    def location_info
      location = [ profile.city, profile.state, profile.country ].compact.join(", ")
      return nil if location.blank?

      "location: #{location}"
    end

    def work_preferences
      preferences = []
      preferences << "remote_work: #{profile.remote_work ? 'yes' : 'no'}" unless profile.remote_work.nil?
      preferences << "mobility: #{profile.mobility ? 'yes' : 'no'}" unless profile.mobility.nil?
      preferences.join(" | ").presence
    end

    def salary_info
      salaries = []
      salaries << "clt_expectation: #{profile.clt_expectation}" if profile.clt_expectation.present?
      salaries << "pj_expectation: #{profile.pj_expectation}" if profile.pj_expectation.present?
      salaries << "freelance_expectation: #{profile.freelance_expectation}" if profile.freelance_expectation.present?
      salaries.join(" | ").presence
    end

    def skills_list
      skills = profile.expertise.presence || extract_skills_from_data
      return nil if skills.blank?

      "skills: #{Array(skills).compact.uniq.join(', ')}"
    end

    def extract_skills_from_data
      return [] unless profile.skills_data.present?

      profile.skills_data.map do |skill|
        skill.is_a?(Hash) ? skill["name"] : skill
      end.compact
    end

    def experiences_text
      experiences = profile.experiences
      return nil if experiences.blank?

      experiences.map do |exp|
        company = exp.dig("company_info", "name") || exp["company"]
        roles = exp["company_roles"] || []

        roles.map do |role|
          lines = []
          lines << [ role["title"], company ].compact.join(" @ ")
          lines << role["experience_summary"] || role["summary"]
          lines << build_date_range(role["start_date"], role["end_date"])
          lines.compact.join(" | ")
        end
      end.flatten.compact.join("\n")
    end

    def educations_text
      educations = profile.educations
      return nil if educations.blank?

      educations.map do |edu|
        degree = [ edu["degree"], edu["major"] ].compact.join(" - ")
        place = edu["campus"] || edu["institution"]
        date_range = build_date_range(edu["start_date"], edu["end_date"])
        [ degree.presence, place, date_range ].compact.join(" | ")
      end.join("\n")
    end

    def languages_list
      languages = extract_languages_from_data
      return nil if languages.blank?

      "languages: #{languages.join(', ')}"
    end

    def extract_languages_from_data
      return [] unless profile.languages_data.present?

      profile.languages_data.map do |lang|
        lang.is_a?(Hash) ? lang["name"] || lang["language"] : lang
      end.compact
    end

    def links_info
      links = []
      links << "linkedin: #{profile.linkedin_url}" if profile.linkedin_url.present?
      links << "github: #{profile.github}" if profile.github.present?
      links << "portfolio: #{profile.portfolio}" if profile.portfolio.present?
      links.join(" | ").presence
    end

    def build_date_range(start_date, end_date)
      return nil unless start_date || end_date

      start_str = start_date.to_s
      end_str = end_date.to_s
      return start_str if end_str.blank?
      return end_str if start_str.blank?

      "#{start_str} - #{end_str}"
    end
  end
end
