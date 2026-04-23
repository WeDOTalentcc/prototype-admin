# frozen_string_literal: true

module Wsi
  module ReportSchema
    SECTION_KEYS = %w[1 2 3 4 5 6 7 8 9].freeze

    def self.validate!(report)
      errors = validate(report)
      return report if errors.empty?

      raise ArgumentError, "Invalid F11 report: #{errors.join('; ')}"
    end

    def self.validate(report)
      return [ "report must be a Hash" ] unless report.is_a?(Hash)

      errs = []
      errs << "missing report_id" unless report["report_id"].present?
      errs << "missing generated_at" unless report["generated_at"].present?
      errs << "missing methodology_version" unless report["methodology_version"].present?
      errs << "missing report_version" unless report["report_version"].present?
      sections = report["sections"]
      unless sections.is_a?(Hash)
        errs << "sections must be a Hash"
        return errs
      end

      SECTION_KEYS.each do |k|
        errs << "missing sections[#{k}]" unless sections[k].is_a?(Hash)
      end

      g2 = sections["2"]
      if g2.is_a?(Hash) && !g2["gate_checklist"].is_a?(Hash)
        errs << "section 2 gate_checklist must be a Hash"
      end

      g9 = sections["9"]
      if g9.is_a?(Hash)
        errs << "section 9 answers_hash required" unless g9["answers_hash"].to_s.present?
        errs << "section 9 report_version required" unless g9["report_version"].to_s.present?
      end

      errs
    end
  end
end
