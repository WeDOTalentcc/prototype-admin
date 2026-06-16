# frozen_string_literal: true

require "rails_helper"

RSpec.describe DreyfusScorer do
  describe ".evaluate" do
    it "returns a structured hash with level and score" do
      text = "Implementei, liderei o time e entreguei melhoria com redução de 35% no tempo."
      result = described_class.evaluate(text)

      expect(result[:level]).to be_present
      expect(result[:score]).to be_between(1.0, 5.0)
      expect(result[:confidence]).to be_between(0.0, 1.0)
      expect(result[:signals]).to be_a(Hash)
    end
  end

  describe "#call" do
    it "blends with self declaration when provided" do
      scorer = described_class.new(
        response_text: "Resolvi problemas e entreguei resultados com impacto.",
        self_declaration_score: 5.0
      )
      result = scorer.call

      expect(result.score).to be <= 5.0
      expect(result.level).to be_present
    end
  end
end
