# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::QuestionValidator do
  let(:valid_body) do
    "Descreva uma situação profissional em que você teve que organizar várias entregas simultâneas com prazo " \
      "apertado e qualidade em risco. Como você priorizou o trabalho, quais decisões tomou em equipe e qual foi " \
      "o resultado mensurável alcançado no projeto naquele período?"
  end

  describe ".call" do
    it "accepts a situational question with past evidence and word count in range" do
      result = described_class.call(text: valid_body)
      expect(result.valid).to be true
      expect(result.error).to be_nil
    end

    it "rejects too_short" do
      short = "one two three four five six seven eight nine ten"
      result = described_class.call(text: short)
      expect(result.valid).to be false
      expect(result.error).to eq(:too_short)
    end

    it "rejects hypothetical_format" do
      bad = ("Como você faria se o escopo mudasse no meio do sprint? " * 5).strip
      result = described_class.call(text: bad)
      expect(result.valid).to be false
      expect(result.error).to eq(:hypothetical_format)
    end

    it "rejects imagine que" do
      bad = ("Imagine que você precisasse liderar um time sem autoridade formal. " * 4).strip
      result = described_class.call(text: bad)
      expect(result.valid).to be false
      expect(result.error).to eq(:hypothetical_format)
    end
  end
end
