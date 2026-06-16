# frozen_string_literal: true

module Wsi
  class QuestionDistributionService
    def self.call(seniority_key:, mode:)
      new(seniority_key: seniority_key, mode: mode).call
    end

    def self.framework_allocation(technical:, behavioral:, mode:)
      m = mode.to_sym
      raise ArgumentError, "mode must be :compact or :full" unless %i[compact full].include?(m)

      t = technical.to_i
      b = behavioral.to_i

      if m == :compact
        allocation_compact(t, b)
      else
        allocation_full(t, b)
      end
    end

    def self.allocation_compact(t, b)
      dreyfus = t >= 2 ? 1 : 0
      bloom = t >= 3 ? 1 : 0
      cbi_technical = [ t - dreyfus - bloom, 1 ].max
      cbi_behavioral = 1
      big_five = b - 1

      {
        dreyfus: dreyfus,
        bloom: bloom,
        cbi_technical: cbi_technical,
        cbi_behavioral: cbi_behavioral,
        big_five: big_five
      }
    end

    def self.allocation_full(t, b)
      dreyfus = [ t - 3, 0 ].max.clamp(0, 2)
      bloom = [ t - 1 - dreyfus, 0 ].max.clamp(0, 2)
      cbi_technical = [ t - dreyfus - bloom, 1 ].max
      cbi_behavioral = [ b - 2, 1 ].max
      big_five = b - cbi_behavioral

      {
        dreyfus: dreyfus,
        bloom: bloom,
        cbi_technical: cbi_technical,
        cbi_behavioral: cbi_behavioral,
        big_five: big_five
      }
    end

    private_class_method :allocation_compact, :allocation_full

    def initialize(seniority_key:, mode:)
      @seniority_key = seniority_key.to_s
      @mode = mode.to_sym
    end

    def call
      raise ArgumentError, "mode must be :compact or :full" unless %i[compact full].include?(@mode)

      row = Wsi::Constants.question_distribution_row(@seniority_key, @mode)
      {
        technical: row[:technical],
        behavioral: row[:behavioral],
        top_n_traits: row[:top_n_traits]
      }
    end
  end
end
