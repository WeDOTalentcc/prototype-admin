# frozen_string_literal: true

require "rails_helper"

RSpec.describe BloomClassifier do
  describe ".classify" do
    it "returns create for innovation-oriented answers" do
      text = "Eu criei uma nova arquitetura e inovei no fluxo para melhorar o resultado."
      expect(described_class.classify(text)).to eq("create")
    end

    it "returns apply for implementation-oriented answers" do
      text = "Implementei a solução, configurei o ambiente e executei os testes."
      expect(described_class.classify(text)).to eq("apply")
    end
  end

  describe "#call" do
    it "returns a structured result with confidence" do
      result = described_class.new(response_text: "Analisei o problema e comparei os cenários.").call

      expect(result.level).to eq("analyze")
      expect(result.score).to be_between(1, 5)
      expect(result.confidence).to be_between(0.0, 1.0)
    end
  end
end
