# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::QuestionDistributionService do
  describe ".call" do
    [
      { seniority: "junior", mode: :compact, technical: 5, behavioral: 2, top_n_traits: 2 },
      { seniority: "lead", mode: :compact, technical: 3, behavioral: 4, top_n_traits: 4 },
      { seniority: "senior", mode: :full, technical: 7, behavioral: 5, top_n_traits: 5 }
    ].each do |row|
      it "returns T/B/Top-N for #{row[:seniority]} #{row[:mode]}" do
        result = described_class.call(seniority_key: row[:seniority], mode: row[:mode])
        expect(result[:technical]).to eq(row[:technical])
        expect(result[:behavioral]).to eq(row[:behavioral])
        expect(result[:top_n_traits]).to eq(row[:top_n_traits])
      end
    end

    it "covers all seniority keys in QUESTION_DISTRIBUTIONS for both modes" do
      keys = Wsi::Constants::QUESTION_DISTRIBUTIONS[:compact].keys
      keys.each do |key|
        compact = described_class.call(seniority_key: key, mode: :compact)
        full = described_class.call(seniority_key: key, mode: :full)
        expect(compact[:technical] + compact[:behavioral]).to eq(7)
        expect(full[:technical] + full[:behavioral]).to eq(12)
      end
    end
  end

  describe ".framework_allocation" do
    context "compact mode" do
      it "matches methodology §5.8 examples" do
        expect(described_class.framework_allocation(technical: 5, behavioral: 2, mode: :compact)).to eq(
          dreyfus: 1,
          bloom: 1,
          cbi_technical: 3,
          cbi_behavioral: 1,
          big_five: 1
        )

        expect(described_class.framework_allocation(technical: 4, behavioral: 3, mode: :compact)).to eq(
          dreyfus: 1,
          bloom: 1,
          cbi_technical: 2,
          cbi_behavioral: 1,
          big_five: 2
        )

        expect(described_class.framework_allocation(technical: 3, behavioral: 4, mode: :compact)).to eq(
          dreyfus: 1,
          bloom: 1,
          cbi_technical: 1,
          cbi_behavioral: 1,
          big_five: 3
        )

        expect(described_class.framework_allocation(technical: 2, behavioral: 5, mode: :compact)).to eq(
          dreyfus: 1,
          bloom: 0,
          cbi_technical: 1,
          cbi_behavioral: 1,
          big_five: 4
        )
      end
    end

    context "full mode" do
      it "matches methodology §5.8 examples" do
        expect(described_class.framework_allocation(technical: 9, behavioral: 3, mode: :full)).to eq(
          dreyfus: 2,
          bloom: 2,
          cbi_technical: 5,
          cbi_behavioral: 1,
          big_five: 2
        )

        expect(described_class.framework_allocation(technical: 8, behavioral: 4, mode: :full)).to eq(
          dreyfus: 2,
          bloom: 2,
          cbi_technical: 4,
          cbi_behavioral: 2,
          big_five: 2
        )

        expect(described_class.framework_allocation(technical: 7, behavioral: 5, mode: :full)).to eq(
          dreyfus: 2,
          bloom: 2,
          cbi_technical: 3,
          cbi_behavioral: 3,
          big_five: 2
        )
      end
    end

    it "raises for invalid mode" do
      expect do
        described_class.framework_allocation(technical: 5, behavioral: 2, mode: :wide)
      end.to raise_error(ArgumentError, /mode must be :compact or :full/)
    end
  end
end
