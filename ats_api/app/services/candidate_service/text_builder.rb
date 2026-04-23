module CandidateService
  class TextBuilder
    MAX_CHARS = 8000

    def self.call(c)
      sections = []

      # === HEADER (always included, never truncated) ===
      header = build_header(c)
      sections << { priority: 1, content: header }

      # === CURRICULUM (prioridade alta: campo mais importante para busca/embedding; evitar truncar) ===
      if c.curriculum_text.present?
        sections << { priority: 2, content: "Resume: #{c.curriculum_text}" }
      end

      # === SKILLS (high priority for matching) ===
      if c.respond_to?(:skills) && c.skills.any?
        skills_text = c.skills.map(&:name).compact.uniq.join(", ")
        sections << { priority: 3, content: "Skills: #{skills_text}" } if skills_text.present?
      end

      # === SELF INTRODUCTION ===
      if c.self_introduction.present?
        sections << { priority: 4, content: c.self_introduction }
      end

      # === EXPERIENCES with contract_type ===
      exp_section = build_experiences(c)
      sections << { priority: 5, content: exp_section } if exp_section.present?

      # === EDUCATIONS ===
      edu_section = build_educations(c)
      sections << { priority: 6, content: edu_section } if edu_section.present?

      # === LANGUAGES ===
      lang_section = build_languages(c)
      sections << { priority: 7, content: lang_section } if lang_section.present?

      # === OTHER METADATA (menor prioridade; pode ser truncado) ===
      metadata = build_metadata(c)
      sections << { priority: 8, content: metadata } if metadata.present?

      # === SMART TRUNCATION ===
      assemble_with_truncation(sections)
    end

    private

    def self.build_header(c)
      parts = []
      parts << c.name.to_s.presence || "Candidate"

      headline = [ c.role_name, c.position_level ].compact.join(" · ")
      parts << headline if headline.present?

      parts << "at #{c.current_company}" if c.current_company.present?

      loc = [ c.city, c.state, c.country ].compact.join(", ")
      parts << loc if loc.present?

      # Total years of experience
      total_years = calculate_total_experience(c)
      parts << "#{total_years} years of experience" if total_years > 0

      parts.join(" | ")
    end

    def self.build_experiences(c)
      return nil unless c.respond_to?(:experiences) && c.experiences.any?

      exp_texts = c.experiences.order(end_date: :desc).limit(5).map do |exp|
        role = exp.occupation&.name || "Role"
        company = exp.company&.name || "Company"
        duration = format_duration(exp.start_date, exp.end_date, exp.work_here)
        contract = exp.contract_type.present? ? " (#{exp.contract_type})" : ""
        desc = exp.description.to_s.truncate(250, omission: "...")

        "#{role} at #{company}#{contract}, #{duration}: #{desc}".strip
      end

      return nil if exp_texts.empty?
      "Experience: #{exp_texts.join(' | ')}"
    end

    def self.build_educations(c)
      return nil unless c.respond_to?(:educations) && c.educations.any?

      edu_texts = c.educations.order(end_date: :desc).limit(3).map do |edu|
        institution = edu.institution&.name || "Institution"
        area = edu.study_area&.name
        level = format_education_level(edu.formation_type)
        [ level, area, "at #{institution}" ].compact.join(" ")
      end

      return nil if edu_texts.empty?
      "Education: #{edu_texts.join(' | ')}"
    end

    def self.build_languages(c)
      return nil unless c.respond_to?(:language_relationships) && c.language_relationships.any?

      lang_texts = c.language_relationships.map do |lr|
        next unless lr.language&.name.present?
        level = lr.level.present? ? " (#{lr.level})" : ""
        "#{lr.language.name}#{level}"
      end.compact

      return nil if lang_texts.empty?
      "Languages: #{lang_texts.join(', ')}"
    end

    def self.build_metadata(c)
      parts = []
      parts << "interests: #{c.interests}" if c.interests.present?
      parts << "remote: #{c.remote_work ? 'yes' : 'no'}" unless c.remote_work.nil?
      parts << "mobility: #{c.mobility ? 'yes' : 'no'}" unless c.mobility.nil?

      if c.current_salary.to_f > 0 || c.desired_salary.to_f > 0
        salary = [
          (c.current_salary.to_f > 0 && "current: #{c.current_salary}"),
          (c.desired_salary.to_f > 0 && "desired: #{c.desired_salary}")
        ].compact.join(", ")
        parts << "salary (#{c.currency || 'BRL'}): #{salary}"
      end

      parts << "source: #{c.source}" if c.source.present?
      parts.join(" | ")
    end

    def self.calculate_total_experience(c)
      return 0 unless c.respond_to?(:experiences)

      total_months = c.experiences.sum do |exp|
        start_date = exp.start_date
        end_date = exp.work_here ? Date.current : exp.end_date
        next 0 unless start_date && end_date

        ((end_date.year * 12 + end_date.month) - (start_date.year * 12 + start_date.month)).abs
      end

      (total_months / 12.0).round
    rescue
      0
    end

    def self.assemble_with_truncation(sections)
      # Sort by priority (lower = more important)
      sorted = sections.sort_by { |s| s[:priority] }

      result = []
      remaining = MAX_CHARS

      sorted.each do |section|
        content = section[:content].to_s.strip
        next if content.empty?

        if content.length <= remaining
          result << content
          remaining -= content.length + 2 # +2 for \n\n separator
        elsif section[:priority] >= 5 && remaining > 100
          # Lower priority sections can be truncated
          result << content.truncate(remaining, omission: "...")
          remaining = 0
        end

        break if remaining <= 0
      end

      result.join("\n\n")
    end

    def self.format_duration(start_date, end_date, is_current)
      return "" unless start_date
      start_year = start_date.year rescue nil
      end_year = is_current ? "present" : (end_date&.year rescue nil)
      [ start_year, end_year ].compact.join("-")
    end

    def self.format_education_level(formation_type)
      case formation_type.to_i
      when 1 then "Elementary"
      when 2 then "High School"
      when 3 then "Technical"
      when 4 then "Associate"
      when 5 then "Bachelor's"
      when 6 then "Teaching"
      when 7 then "Postgraduate"
      when 8 then "Master's"
      when 9 then "PhD"
      end
    end
  end
end
