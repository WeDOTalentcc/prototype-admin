# frozen_string_literal: true

require "rails_helper"

RSpec.describe BigFiveAnalyzer do
  describe ".analyze" do
    it "returns all OCEAN dimensions and confidence" do
      text = "Colaborei com o time, planejei o processo, comuniquei riscos e lidei com pressão."
      result = described_class.analyze(text)

      expect(result).to include(:o, :c, :e, :a, :n, :confidence)
      expect(result[:o]).to be_between(1.0, 5.0)
      expect(result[:c]).to be_between(1.0, 5.0)
      expect(result[:e]).to be_between(1.0, 5.0)
      expect(result[:a]).to be_between(1.0, 5.0)
      expect(result[:n]).to be_between(1.0, 5.0)
      expect(result[:confidence]).to be_between(0.0, 1.0)
    end
  end
end
