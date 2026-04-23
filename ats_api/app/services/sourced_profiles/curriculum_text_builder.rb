module SourcedProfiles
  class CurriculumTextBuilder
    def self.build(profile_data:, result: {})
      new(profile_data: profile_data, result: result).build
    end

    def initialize(profile_data:, result: {})
      @profile = profile_data || {}
      @result = result || {}
    end

    def build
      parts = [ header, summary, skills, experiences, educations, certifications, languages, extras ]
      parts = parts.flatten.compact.map(&:strip).reject(&:empty?)
      return nil if parts.empty?
      parts.join("\n\n")
    end

    private

    attr_reader :profile, :result

    def header
      [ profile[:name], profile[:title], profile[:location] ].compact.join(" | ").presence
    end

    def summary
      profile[:summary].presence
    end

    def skills
      list = profile[:expertise] || profile[:skills]
      return nil if list.blank?
      "Skills: #{Array(list).compact.uniq.join(', ')}"
    end

    def experiences
      entries = profile[:experiences] || []
      return nil if entries.empty?

      entries.map do |exp|
        company = exp.dig(:company_info, :name)
        roles = exp[:company_roles] || []
        roles.map do |role|
          lines = []
          lines << [ role[:title], company ].compact.join(" @ ")
          lines << role[:experience_summary]
          lines << date_range(role[:start_date], role[:end_date])
          lines.compact.join(" | ")
        end
      end.flatten.compact.join("\n")
    end

    def educations
      entries = profile[:educations] || []
      return nil if entries.empty?

      entries.map do |edu|
        degree = [ edu[:degree], edu[:major] ].compact.join(" - ")
        place = edu[:campus] || edu[:institution]
        [ degree.presence, place, date_range(edu[:start_date], edu[:end_date]) ].compact.join(" | ")
      end.join("\n")
    end

    def certifications
      list = profile[:certifications]
      return nil if list.blank?
      titled("Certifications", list)
    end

    def languages
      list = profile[:languages]
      return nil if list.blank?
      titled("Languages", list.map { |l| [ l[:language], l[:proficiency] ].compact.join(" - ") })
    end

    def extras
      parts = [ profile[:resume_text], profile[:resume], profile[:cv_text], result[:curriculum_text], result[:resume_text], result[:resume] ]
      parts = parts.compact.map { |t| t.is_a?(String) ? t.strip : t }
      parts.reject(&:blank?).first
    end

    def date_range(start_date, end_date)
      return nil unless start_date || end_date
      start_str = start_date.to_s
      end_str = end_date.to_s
      return start_str if end_str.blank?
      return end_str if start_str.blank?
      "#{start_str} - #{end_str}"
    end

    def titled(label, items)
      body = Array(items).compact.uniq
      return nil if body.empty?
      "#{label}: #{body.join(', ')}"
    end
  end
end
