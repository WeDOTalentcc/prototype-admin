# frozen_string_literal: true

require "rails_helper"

RSpec.describe JobSuggestionService do
  TRAITS = Wsi::JdBigFiveExtractionService::TRAITS

  def build_big_five_jd(scores_by_trait)
    TRAITS.index_with do |trait|
      { "score" => scores_by_trait.fetch(trait), "evidence" => [], "confidence" => "high" }
    end
  end

  describe ".ensure_wsi_jd_trait_ranking!" do
    let(:scores) do
      {
        "openness" => 74,
        "conscientiousness" => 76,
        "extraversion" => 40,
        "agreeableness" => 50,
        "stability" => 75
      }
    end

    it "persists compact ranking for wsi_compact" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.ensure_wsi_jd_trait_ranking!(job, wsi_type: "wsi_compact")
      expect(job.reload.wsi_jd_trait_ranking["mode"]).to eq("compact")
      expect(job.wsi_jd_trait_ranking["top_n"]).to eq(3)
    end

    it "persists full ranking for wsi_compact_plus" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.ensure_wsi_jd_trait_ranking!(job, wsi_type: "wsi_compact_plus")
      expect(job.reload.wsi_jd_trait_ranking["mode"]).to eq("full")
      expect(job.wsi_jd_trait_ranking["top_n"]).to eq(5)
    end

    it "uses compact for query type" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.ensure_wsi_jd_trait_ranking!(job, wsi_type: "query")
      expect(job.reload.wsi_jd_trait_ranking["mode"]).to eq("compact")
    end
  end

  describe "evaluation questions prompt (F5 distribution)" do
    let(:scores) do
      {
        "openness" => 74,
        "conscientiousness" => 76,
        "extraversion" => 40,
        "agreeableness" => 50,
        "stability" => 75
      }
    end

    it "embeds lead compact plan and canonical weights in the prompt" do
      job = create(:job, seniority: 5, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.ensure_wsi_jd_trait_ranking!(job, wsi_type: "wsi_compact")
      job_data = described_class.build_job_data_for_evaluation(job, wsi_type: "wsi_compact")
      service = described_class.new(job_data: job_data, type: "evaluation_questions", wsi_type: "wsi_compact")
      prompt = service.send(:prompt_for_evaluation_questions, "")

      expect(prompt).to include("3 perguntas técnicas")
      expect(prompt).to include("4 comportamentais")
      expect(prompt).to include("0.4375")
      expect(prompt).to include("0.5625")
      expect(prompt).to include("Dreyfus 1")
      expect(prompt).not_to include("70% competências técnicas / 30%")
    end

    it "embeds senior full plan for wsi_compact_plus" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.ensure_wsi_jd_trait_ranking!(job, wsi_type: "wsi_compact_plus")
      job_data = described_class.build_job_data_for_evaluation(job, wsi_type: "wsi_compact_plus")
      service = described_class.new(job_data: job_data, type: "evaluation_questions", wsi_type: "wsi_compact_plus")
      prompt = service.send(:prompt_for_evaluation_questions, "")

      expect(prompt).to include("7 perguntas técnicas")
      expect(prompt).to include("5 comportamentais")
      expect(prompt).to include("Gere exatamente entre 12 e 12 perguntas")
    end
  end

  describe ".generate_evaluation_questions" do
    let(:scores) do
      {
        "openness" => 74,
        "conscientiousness" => 76,
        "extraversion" => 40,
        "agreeableness" => 50,
        "stability" => 75
      }
    end

    it "passes job into the service so JD anchoring can run after generation" do
      job = create(:job, seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => build_big_five_jd(scores) })
      described_class.ensure_wsi_jd_trait_ranking!(job, wsi_type: "wsi_compact")

      expect(described_class).to receive(:new).with(
        job_data: kind_of(Hash),
        type: "evaluation_questions",
        wsi_type: "wsi_compact",
        query: nil,
        job: job
      ).and_call_original

      allow_any_instance_of(described_class).to receive(:generate_with_gemini).and_return(
        described_class::Result.new(true, { questions: [] }, nil)
      )

      described_class.generate_evaluation_questions(job, wsi_type: "wsi_compact")
    end
  end
end
