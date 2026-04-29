# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::TraitRankingService do
  TRAITS = Wsi::JdBigFiveExtractionService::TRAITS

  def build_big_five_jd(scores_by_trait)
    TRAITS.index_with do |trait|
      { "score" => scores_by_trait.fetch(trait), "evidence" => [], "confidence" => "high" }
    end
  end

  describe ".call" do
    it "ranks traits by score, sets top_n for senior compact, normalizes weights on top-N, and persists" do
      scores = {
        "openness" => 74,
        "conscientiousness" => 76,
        "extraversion" => 40,
        "agreeableness" => 50,
        "stability" => 75
      }
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })

      result = described_class.call(job: job, mode: :compact)

      expect(result[:success]).to be true
      job.reload
      expect(job.wsi_jd_trait_ranking).to be_present
      expect(job.wsi_jd_trait_ranking["method_version"]).to eq("wsi_f3_v1")
      expect(job.wsi_jd_trait_ranking["mode"]).to eq("compact")
      expect(job.wsi_jd_trait_ranking["seniority_key"]).to eq("senior")
      expect(job.wsi_jd_trait_ranking["top_n"]).to eq(3)

      rows = job.wsi_jd_trait_ranking["big_five_ranking"]
      expect(rows[0]["trait"]).to eq("conscientiousness")
      expect(rows[0]["rank"]).to eq(1)
      expect(rows[0]["in_top_n"]).to be true

      top_three = rows.select { |r| r["in_top_n"] }
      expect(top_three.size).to eq(3)
      sum = top_three.sum { |r| r["weight_normalized"] }
      expect(sum).to be_within(1e-9).of(1.0)

      expect(rows[3]["in_top_n"]).to be false
      expect(rows[3]["weight_normalized"]).to eq(0.0)
      expect(rows[4]["weight_normalized"]).to eq(0.0)
    end

    it "returns failure when big_five_jd is missing" do
      job = create(:job, description: "x", wsi_jd_big_five_profile: {})
      result = described_class.call(job: job, mode: :compact)
      expect(result[:success]).to be false
      expect(result[:code]).to eq("wsi_trait_ranking_profile_missing")
    end

    it "returns failure when mode is invalid" do
      uniform = TRAITS.index_with { 50 }
      job = create(:job, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(uniform) })
      result = described_class.call(job: job, mode: :invalid)
      expect(result[:success]).to be false
      expect(result[:code]).to eq("wsi_trait_ranking_mode_invalid")
    end
  end

  describe ".trait_weight_for" do
    let(:scores) do
      {
        "openness" => 74,
        "conscientiousness" => 76,
        "extraversion" => 40,
        "agreeableness" => 50,
        "stability" => 75
      }
    end

    it "returns weight_normalized for the trait from persisted ranking (storage form)" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.call(job: job, mode: :compact)
      job.reload

      stored = job.wsi_jd_trait_ranking["big_five_ranking"].find { |r| r["trait"] == "conscientiousness" }["weight_normalized"]
      expect(described_class.trait_weight_for(job: job, ocean_trait: "conscientiousness")).to eq(stored)
    end

    it "resolves neuroticism storage to stability in ranking" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.call(job: job, mode: :compact)
      job.reload

      stored = job.wsi_jd_trait_ranking["big_five_ranking"].find { |r| r["trait"] == "stability" }["weight_normalized"]
      expect(described_class.trait_weight_for(job: job, ocean_trait: "neuroticism")).to eq(stored)
    end

    it "returns 1.0 when job is nil" do
      expect(described_class.trait_weight_for(job: nil, ocean_trait: "conscientiousness")).to eq(1.0)
    end

    it "returns 1.0 when ranking is missing" do
      job = create(:job, wsi_jd_trait_ranking: {})
      expect(described_class.trait_weight_for(job: job, ocean_trait: "conscientiousness")).to eq(1.0)
    end

    it "returns 1.0 when ocean_trait is blank" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.call(job: job, mode: :compact)
      job.reload
      expect(described_class.trait_weight_for(job: job, ocean_trait: "")).to eq(1.0)
    end
  end
end
