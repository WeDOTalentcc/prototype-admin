# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::PiiMasker do
  describe ".call" do
    it "replaces CPF with removal token" do
      masked = described_class.call(text: "Contato: CPF 123.456.789-00")

      expect(masked).not_to include("123.456.789")
      expect(masked).to include("[CPF REMOVIDO]")
    end

    it "replaces email with removal token" do
      masked = described_class.call(text: "me escreva em a@b.co para retorno")

      expect(masked).to include("[EMAIL REMOVIDO]")
      expect(masked).not_to include("a@b.co")
    end

    it "replaces Portuguese preposition surnames with removal token" do
      masked = described_class.call(text: "Contato: João da Silva")

      expect(masked).not_to include("João")
      expect(masked).not_to include("Silva")
      expect(masked).to include("[NOME REMOVIDO]")
    end

    it "replaces name in nome=/name= log-style fragments" do
      masked = described_class.call(text: 'nome: "Maria Santos" para retorno')

      expect(masked).not_to include("Maria Santos")
      expect(masked).to include("[NOME REMOVIDO]")
    end

    it "does not mask two title-case words that are not Portuguese surname pattern" do
      masked = described_class.call(text: "Benefício: Vale Refeição incluído")

      expect(masked).to include("Vale Refeição")
    end
  end
end
