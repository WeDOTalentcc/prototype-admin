# frozen_string_literal: true

module Wsi
  class TraitAffinitySelector
    TRAIT_ALIASES = {
      "neuroticism" => "stability",
      "emotional_stability" => "stability",
      "stability" => "stability"
    }.freeze

    def initialize(target_trait:, behavioral_competencies:, used_indices: [])
      @target_trait = normalize_trait(target_trait)
      @competencies = Array(behavioral_competencies).map { |entry| normalize_competency_entry(entry) }
      @used_indices = used_indices.to_set
    end

    def call
      return empty_result if @competencies.empty?

      match_idx = @competencies.each_with_index.find do |_comp, idx|
        next false if @used_indices.include?(idx)

        comp_trait = @competencies[idx][:trait]
        comp_trait.present? && comp_trait == @target_trait
      end&.last

      return result_at(match_idx) if match_idx

      fallback_idx = @competencies.each_with_index.find { |_c, idx| !@used_indices.include?(idx) }&.last
      return result_at(fallback_idx) if fallback_idx

      result_at(0)
    end

    private

    def empty_result
      { name: nil, index: nil, trait: nil }
    end

    def result_at(index)
      comp = @competencies[index]
      { name: comp[:name], index: index, trait: comp[:trait] }
    end

    def normalize_trait(raw)
      s = raw.to_s.strip.downcase
      TRAIT_ALIASES[s] || s
    end

    def normalize_competency_entry(entry)
      return { name: entry.to_s, trait: nil } unless entry.is_a?(Hash)

      h = entry.stringify_keys
      name = h["competencia"].presence || h["name"].presence || h["competency"].presence || ""
      trait_raw = h["trait_big_five"].presence || h["big_five_mapping"].presence
      trait = trait_raw.present? ? normalize_trait(trait_raw) : nil
      { name: name.to_s, trait: trait }
    end
  end
end
