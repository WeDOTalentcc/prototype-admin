# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Llm::CostCalculator do
  describe '.calculate' do
    context 'with Gemini models' do
      it 'calculates cost for gemini-2.5-flash' do
        cost = described_class.calculate(
          model: "gemini-2.5-flash",
          input_tokens: 1_000_000,
          output_tokens: 1_000_000
        )

        expect(cost).to eq(0.375)
      end

      it 'calculates cost for gemini-1.5-pro' do
        cost = described_class.calculate(
          model: "gemini-1.5-pro",
          input_tokens: 1_000_000,
          output_tokens: 1_000_000
        )

        expect(cost).to eq(6.25)
      end

      it 'calculates cost for gemini-embedding-001' do
        cost = described_class.calculate(
          model: "gemini-embedding-001",
          input_tokens: 1_000,
          output_tokens: 0
        )

        expect(cost).to eq(0.00001)
      end
    end

    context 'with OpenAI models' do
      it 'calculates cost for gpt-4o' do
        cost = described_class.calculate(
          model: "gpt-4o",
          input_tokens: 1_000_000,
          output_tokens: 1_000_000
        )

        expect(cost).to eq(12.5)
      end

      it 'calculates cost for text-embedding-3-small' do
        cost = described_class.calculate(
          model: "text-embedding-3-small",
          input_tokens: 1_000_000,
          output_tokens: 0
        )

        expect(cost).to eq(0.02)
      end
    end

    context 'with small token counts' do
      it 'calculates fractional costs accurately' do
        cost = described_class.calculate(
          model: "gemini-2.5-flash",
          input_tokens: 1000,
          output_tokens: 500
        )

        expect(cost).to be > 0
        expect(cost).to be < 0.001
      end
    end

    context 'with unknown model' do
      it 'returns 0.0' do
        cost = described_class.calculate(
          model: "unknown-model",
          input_tokens: 1000,
          output_tokens: 1000
        )

        expect(cost).to eq(0.0)
      end
    end
  end

  describe '.estimate_tokens' do
    it 'estimates tokens for short text' do
      tokens = described_class.estimate_tokens("Hello world")
      expect(tokens).to eq(3)
    end

    it 'estimates tokens for longer text' do
      text = "This is a longer piece of text that should have more tokens"
      tokens = described_class.estimate_tokens(text)
      expect(tokens).to be > 10
    end

    it 'returns 0 for blank text' do
      expect(described_class.estimate_tokens("")).to eq(0)
      expect(described_class.estimate_tokens(nil)).to eq(0)
    end
  end
end
