require "rails_helper"

RSpec.describe SourcedProfileAnalysisService, type: :service do
  let(:account) { create(:account) }
  let(:sourced_profile) do
    create(:sourced_profile,
           account: account,
           name: "Ada Lovelace")
  end

  subject(:service) { described_class.new(sourced_profile: sourced_profile, account: account) }

  describe "#call" do
    before do
      allow(service).to receive(:invoke_llm).and_return(
        summary: "Senior dev with strong Rails background",
        skills_analysis: { strong: %w[ruby rails], moderate: [], gaps: [] },
        fit_score: 0.82,
        strengths: [ "Direct stack match" ],
        concerns: []
      )
      Rails.cache.clear
    end

    it "returns the analysis hash" do
      result = service.call
      expect(result[:summary]).to include("Senior")
      expect(result[:fit_score]).to eq(0.82)
    end

    it "caches the result under sp_analysis:<id>" do
      service.call
      cached = Rails.cache.read(format(described_class::CACHE_KEY, id: sourced_profile.id))
      expect(cached).not_to be_nil
      expect(cached[:fit_score]).to eq(0.82)
    end

    it "returns cached value on second call without re-invoking LLM" do
      service.call
      expect(service).not_to receive(:invoke_llm)
      second = service.call
      expect(second[:fit_score]).to eq(0.82)
    end
  end
end
