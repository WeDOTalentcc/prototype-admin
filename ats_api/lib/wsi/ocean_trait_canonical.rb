# frozen_string_literal: true

module Wsi
  module OceanTraitCanonical
    STABILITY_ALIASES = %w[stability neuroticism].freeze
    STORAGE_TRAIT = "neuroticism"
    API_TRAIT = "stability"

    module_function

    def to_api(trait)
      return nil if trait.blank?

      key = trait.to_s.downcase.strip
      return API_TRAIT if STABILITY_ALIASES.include?(key)

      key
    end

    def to_storage(trait)
      return nil if trait.blank?

      key = trait.to_s.downcase.strip
      return STORAGE_TRAIT if STABILITY_ALIASES.include?(key)

      key
    end
  end
end
