# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::RationaleEvidenceBuilder do
  let(:source) do
    "Situação: havia atrasos. Ação: implementei automação. Resultado: redução de 30%."
  end

  describe ".call" do
    it "returns two ordered literal substrings from rationale, trait excerpts, and key_quote" do
      extraction = {
        rationale: [ "implementei automação" ],
        trait_signals_detected: [ 'impact — excerpt: "redução de 30%"' ],
        key_quote: "\"implementei automação\""
      }

      result = described_class.call(extraction: extraction, source_text: source)

      expect(result).to eq([ "implementei automação", "redução de 30%" ])
    end

    it "returns empty array when fewer than two verified substrings exist" do
      extraction = {
        rationale: [ "implementei automação" ],
        trait_signals_detected: [],
        key_quote: "\"implementei automação\""
      }

      result = described_class.call(extraction: extraction, source_text: source)

      expect(result).to eq([])
    end

    it "rejects strings that do not appear verbatim in the source" do
      extraction = {
        rationale: [ "not in text", "also fake" ],
        trait_signals_detected: [],
        key_quote: ""
      }

      result = described_class.call(extraction: extraction, source_text: source)

      expect(result).to eq([])
    end

    it "parses trecho: style trait lines" do
      extraction = {
        trait_signals_detected: [ 'x — trecho: "implementei automação"', 'y — trecho: "redução de 30%"' ],
        key_quote: ""
      }

      result = described_class.call(extraction: extraction, source_text: source)

      expect(result.size).to eq(2)
    end
  end
end
