# frozen_string_literal: true

require "rails_helper"

RSpec.describe CbiEvaluator do
  describe ".extract_star" do
    it "extracts STAR sections from response" do
      text = <<~TEXT
        Situação: O fechamento financeiro atrasava mensalmente.
        Tarefa: Reduzir o tempo do processo em duas semanas.
        Ação: Automatizei lançamentos e revisei regras de contabilização.
        Resultado: O tempo caiu 40% e os erros reduziram significativamente.
      TEXT

      star = described_class.extract_star(text)

      expect(star[:situation]).to be_present
      expect(star[:task]).to be_present
      expect(star[:action]).to be_present
      expect(star[:result]).to be_present
    end
  end

  describe "#call" do
    it "applies word penalty for fewer than 30 words" do
      words = Array.new(25) { "palavra" }.join(" ")
      result = described_class.new(response_text: words).call

      expect(result[:word_count]).to eq(25)
      expect(result[:star_penalty_words]).to eq(-2.5)
    end

    it "applies first-person penalty when no first-person cues" do
      text = "O processo foi concluído com sucesso pela equipe responsável pelo projeto."
      result = described_class.new(response_text: text).call

      expect(result[:star_penalty_no_first_person]).to eq(-1.5)
    end

    it "applies quantified bonus when response includes a percentage metric" do
      text = "Eu implementei a mudança e reduziu em 40% o tempo de deploy."
      result = described_class.new(response_text: text).call

      expect(result[:star_bonus_quantified]).to eq(0.5)
    end

    it "returns weighted star_score between 0 and 1" do
      text = <<~TEXT
        Situação: projeto crítico. Tarefa: estabilizar produção.
        Ação: eu implementei rollback automático. Resultado: redução de 20% em incidentes.
      TEXT
      result = described_class.new(response_text: text).call

      expect(result[:star_score]).to be_between(0.0, 1.0)
    end
  end
end
