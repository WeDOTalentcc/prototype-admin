# frozen_string_literal: true

module Llm
  class CostCalculator
    PRICING = {
      "gemini-2.0-flash" => { input: 0.075, output: 0.30, per: 1_000_000 },
      "gemini-2.5-flash" => { input: 0.075, output: 0.30, per: 1_000_000 },
      "gemini-1.5-flash" => { input: 0.075, output: 0.30, per: 1_000_000 },
      "gemini-1.5-flash-8b" => { input: 0.0375, output: 0.15, per: 1_000_000 },
      "gemini-1.5-pro" => { input: 1.25, output: 5.00, per: 1_000_000 },
      "gemini-2.0-flash-thinking" => { input: 0.075, output: 0.30, per: 1_000_000 },
      "gemini-embedding-001" => { input: 0.00001, output: 0, per: 1_000 },
      "text-embedding-3-small" => { input: 0.02, output: 0, per: 1_000_000 },
      "text-embedding-3-large" => { input: 0.13, output: 0, per: 1_000_000 },
      "text-embedding-ada-002" => { input: 0.10, output: 0, per: 1_000_000 },
      "gpt-4o" => { input: 2.50, output: 10.00, per: 1_000_000 },
      "gpt-4o-mini" => { input: 0.15, output: 0.60, per: 1_000_000 },
      "gpt-4-turbo" => { input: 10.00, output: 30.00, per: 1_000_000 },
      "gpt-3.5-turbo" => { input: 0.50, output: 1.50, per: 1_000_000 }
    }.freeze

    def self.calculate(model:, input_tokens:, output_tokens:)
      pricing = PRICING[model]

      return 0.0 unless pricing

      input_cost = (input_tokens.to_f / pricing[:per]) * pricing[:input]
      output_cost = (output_tokens.to_f / pricing[:per]) * pricing[:output]

      (input_cost + output_cost).round(8)
    end

    def self.estimate_tokens(text)
      return 0 if text.blank?
      (text.length / 4.0).ceil
    end
  end
end
