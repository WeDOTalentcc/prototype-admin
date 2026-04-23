# frozen_string_literal: true

module Wsi
  module Constants
    SENIORITY_KEY_MAP = {
      0 => "junior",
      1 => "pleno",
      2 => "senior",
      3 => "principal",
      4 => "estagiario",
      5 => "lead",
      6 => "manager",
      7 => "diretor"
    }.freeze

    QUESTION_DISTRIBUTIONS = {
      compact: {
        "estagiario" => { technical: 5, behavioral: 2, top_n_traits: 2 },
        "junior" => { technical: 5, behavioral: 2, top_n_traits: 2 },
        "pleno" => { technical: 5, behavioral: 2, top_n_traits: 2 },
        "senior" => { technical: 4, behavioral: 3, top_n_traits: 3 },
        "lead" => { technical: 3, behavioral: 4, top_n_traits: 4 },
        "principal" => { technical: 4, behavioral: 3, top_n_traits: 3 },
        "diretor" => { technical: 3, behavioral: 4, top_n_traits: 4 },
        "manager" => { technical: 3, behavioral: 4, top_n_traits: 4 },
        "vp_clevel" => { technical: 2, behavioral: 5, top_n_traits: 5 }
      },
      full: {
        "estagiario" => { technical: 9, behavioral: 3, top_n_traits: 3 },
        "junior" => { technical: 9, behavioral: 3, top_n_traits: 3 },
        "pleno" => { technical: 8, behavioral: 4, top_n_traits: 4 },
        "senior" => { technical: 7, behavioral: 5, top_n_traits: 5 },
        "lead" => { technical: 7, behavioral: 5, top_n_traits: 5 },
        "principal" => { technical: 7, behavioral: 5, top_n_traits: 5 },
        "diretor" => { technical: 7, behavioral: 5, top_n_traits: 5 },
        "manager" => { technical: 7, behavioral: 5, top_n_traits: 5 },
        "vp_clevel" => { technical: 7, behavioral: 5, top_n_traits: 5 }
      }
    }.freeze

    SENIORITY_WEIGHTS = {
      "estagiario" => { technical: 0.6875, behavioral: 0.3125 },
      "junior" => { technical: 0.625, behavioral: 0.375 },
      "pleno" => { technical: 0.6875, behavioral: 0.3125 },
      "senior" => { technical: 0.5625, behavioral: 0.4375 },
      "lead" => { technical: 0.4375, behavioral: 0.5625 },
      "principal" => { technical: 0.50, behavioral: 0.50 },
      "diretor" => { technical: 0.3125, behavioral: 0.6875 },
      "vp_clevel" => { technical: 0.25, behavioral: 0.75 },
      "manager" => { technical: 0.3125, behavioral: 0.6875 }
    }.freeze

    SENIORITY_CALIBRATION = {
      "estagiario" => {
        experience_years: "0-1",
        dreyfus_technical_level: 1,
        dreyfus_technical_label: "Novice",
        bloom_expected: "1-2",
        dreyfus_behavioral_level: 1
      },
      "junior" => {
        experience_years: "1-3",
        dreyfus_technical_level: 2,
        dreyfus_technical_label: "Advanced Beginner",
        bloom_expected: "2-3",
        dreyfus_behavioral_level: 2
      },
      "pleno" => {
        experience_years: "3-6",
        dreyfus_technical_level: 3,
        dreyfus_technical_label: "Competent",
        bloom_expected: "4",
        dreyfus_behavioral_level: 3
      },
      "senior" => {
        experience_years: "6-10",
        dreyfus_technical_level: 4,
        dreyfus_technical_label: "Proficient",
        bloom_expected: "5",
        dreyfus_behavioral_level: 4
      },
      "principal" => {
        experience_years: "8-15",
        dreyfus_technical_level: 5,
        dreyfus_technical_label: "Expert",
        bloom_expected: "6",
        dreyfus_behavioral_level: 5
      },
      "lead" => {
        experience_years: "8-15",
        dreyfus_technical_level: 5,
        dreyfus_technical_label: "Expert",
        bloom_expected: "6",
        dreyfus_behavioral_level: 5
      },
      "manager" => {
        experience_years: "8-15",
        dreyfus_technical_level: 5,
        dreyfus_technical_label: "Expert",
        bloom_expected: "6",
        dreyfus_behavioral_level: 5
      },
      "diretor" => {
        experience_years: "10-20",
        dreyfus_technical_level: 5,
        dreyfus_technical_label: "Expert",
        bloom_expected: "6",
        dreyfus_behavioral_level: 5
      },
      "vp_clevel" => {
        experience_years: "15+",
        dreyfus_technical_level: 5,
        dreyfus_technical_label: "Expert",
        bloom_expected: "6",
        dreyfus_behavioral_level: 5
      }
    }.transform_values(&:freeze).freeze

    def self.seniority_calibration(seniority_key)
      key = seniority_key.to_s
      SENIORITY_CALIBRATION[key] || SENIORITY_CALIBRATION.fetch("pleno")
    end

    def self.seniority_key(job)
      return nil if job.nil?

      idx = job.seniority
      return "pleno" if idx.nil?

      SENIORITY_KEY_MAP.fetch(idx.to_i, "pleno")
    end

    def self.big_five_top_n(seniority_key, mode)
      key = seniority_key.to_s
      m = mode.to_sym
      raise ArgumentError, "mode must be :compact or :full" unless %i[compact full].include?(m)

      dist = QUESTION_DISTRIBUTIONS.dig(m, key) || QUESTION_DISTRIBUTIONS.dig(m, "pleno")
      dist.fetch(:top_n_traits)
    end

    def self.question_distribution_row(seniority_key, mode)
      key = seniority_key.to_s
      m = mode.to_sym
      raise ArgumentError, "mode must be :compact or :full" unless %i[compact full].include?(m)

      QUESTION_DISTRIBUTIONS.dig(m, key) || QUESTION_DISTRIBUTIONS.dig(m, "pleno").dup
    end
  end
end
