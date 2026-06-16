# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::SeniorityResolverService do
  describe ".call" do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }

    it "returns senior with high confidence from title when seniority is not set" do
      job = create(:job, account: account, user: user, title: "Senior Software Engineer", seniority: nil, description: nil)
      result = described_class.call(job: job)

      expect(result.success?).to be true
      expect(result.suggested_seniority).to eq("senior")
      expect(result.confidence).to eq("high")
      expect(result.seniority_source).to include("title_keywords")
    end

    it "returns pleno with low confidence for Analista without other qualifiers" do
      job = create(:job, account: account, user: user, title: "Analista de Sistemas", seniority: nil, description: nil)
      result = described_class.call(job: job)

      expect(result.success?).to be true
      expect(result.suggested_seniority).to eq("pleno")
      expect(result.confidence).to eq("low")
    end

    it "returns explicit mapped key with high confidence when seniority is set" do
      job = create(:job, account: account, user: user, title: "Anything", seniority: 2)
      result = described_class.call(job: job)

      expect(result.success?).to be true
      expect(result.suggested_seniority).to eq("senior")
      expect(result.confidence).to eq("high")
      expect(result.seniority_source).to eq([ "explicit" ])
    end

    it "does not persist wsi_suggested_seniority_key on the job" do
      job = create(:job, account: account, user: user, title: "CTO", seniority: nil, description: nil)
      described_class.call(job: job)

      expect(job.reload.wsi_suggested_seniority_key).to be_nil
    end
  end
end
