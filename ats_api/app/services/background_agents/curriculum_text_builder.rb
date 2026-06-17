# frozen_string_literal: true

module BackgroundAgents
  class CurriculumTextBuilder
    def self.call(data:, experiences:, skills:, certifications:, languages:)
      parts = []
      parts << "#{data[:title]} | #{data[:location]}" if data[:title].present?
      parts << "" << data[:summary] if data[:summary].present?

      parts << "" << "Skills: #{skills.join(', ')}" if skills.any?

      experiences.each do |exp|
        company_name = exp.dig("company_info", "name")
        (exp["company_roles"] || []).each do |role|
          line = "#{role['title']} @ #{company_name}"
          line += " | #{role['start_date']}" if role["start_date"]
          parts << "" << line
        end
      end

      certifications.each do |cert|
        title = cert.is_a?(Hash) ? cert["title"] : cert.to_s
        parts << "" << "Certifications: #{title}" if title.present?
      end

      if languages.any?
        lang_str = languages.map { |l|
          l.is_a?(Hash) ? "#{l['language']} - #{l['proficiency']}" : l.to_s
        }.join(", ")
        parts << "" << "Languages: #{lang_str}"
      end

      parts.join("\n").strip
    end
  end
end
