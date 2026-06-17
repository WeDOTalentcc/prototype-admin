# frozen_string_literal: true

module Wsi
  module GeneratedQuestionMetadata
    OCEAN_SKILL_NAME_PT = {
      "openness" => "Abertura",
      "conscientiousness" => "Conscienciosidade",
      "extraversion" => "Extroversão",
      "agreeableness" => "Amabilidade",
      "neuroticism" => "Estabilidade emocional",
      "stability" => "Estabilidade emocional"
    }.freeze

    def self.build(question_data, anchor_skills: [])
      qh = question_data.to_h.with_indifferent_access
      meta = {
        "reviewed_by_recruiter" => false,
        "needs_manual_review" => false,
        "generation_attempts" => 0
      }
      skill = resolve_skill_name(qh, anchor_skills: anchor_skills)
      meta["skill_name"] = skill if skill.present?

      raw = qh[:expected_signals]
      signals = Array(raw).map { |s| s.to_s.strip }.reject(&:blank?)
      meta["expected_signals"] = signals if signals.present?
      meta
    end

    def self.resolve_skill_name(qh, anchor_skills: [])
      explicit = qh[:skill_name].to_s.strip.presence
      return explicit if explicit.present?

      ctype = qh[:competence_type].to_s.downcase
      if ctype == "behavioral"
        trait_key = Wsi::OceanTraitCanonical.to_storage(qh[:ocean_trait])
        label = OCEAN_SKILL_NAME_PT[trait_key] if trait_key.present?
        return label if label.present?
      end

      if ctype == "technical" && anchor_skills.any?
        haystack = "#{qh[:title]} #{qh[:description]}".downcase
        matched = anchor_skills.find { |s| s.present? && haystack.include?(s.to_s.downcase) }
        return matched.to_s.strip if matched.present?
      end

      qh[:title].to_s.strip.presence
    end
    private_class_method :resolve_skill_name
  end
end
