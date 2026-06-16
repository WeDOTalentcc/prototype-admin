# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::JdBigFiveExtractionService do
  TRAITS = Wsi::JdBigFiveExtractionService::TRAITS

  def llm_json_payload(big_five_hash)
    { big_five_jd: big_five_hash }.to_json
  end

  def uniform_traits(score:, evidence:, confidence: "high")
    TRAITS.index_with do |_t|
      { "score" => score, "evidence" => evidence, "confidence" => confidence }
    end
  end

  let(:client) { instance_double(GeminiClient) }

  before do
    allow(GeminiClient).to receive(:new).and_return(client)
  end

  describe ".call" do
    it "persists profile on successful LLM response using job description when LIA not approved" do
      job = create(:job, description: ("word " * 60).strip, lia_job_description: { "status" => "pending_review" })
      payload = uniform_traits(score: 50, evidence: [ '"trecho literal do texto da vaga"' ])
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => llm_json_payload(payload) } } ]
      )

      result = described_class.call(job: job)

      expect(result[:success]).to be true
      job.reload
      expect(job.wsi_jd_big_five_profile["input_source"]).to eq("job_description")
      expect(job.wsi_jd_big_five_profile["method_version"]).to eq("wsi_f25_v1")
      expect(job.wsi_jd_big_five_profile["big_five_jd"].keys.sort).to eq(TRAITS.sort)
    end

    it "uses enriched LIA text when status is approved" do
      enriched = {
        "about_role" => ("roleword " * 30).strip,
        "competencias_comportamentais" => [
          { "competencia" => "Colaboração", "trait_big_five" => "agreeableness" }
        ]
      }
      job = create(
        :job,
        description: "ignored when enriched present",
        lia_job_description: { "status" => "approved", "enriched_jd" => enriched }
      )
      payload = uniform_traits(score: 60, evidence: [ '"evidência"' ])
      captured = nil
      allow(client).to receive(:chat) do |**kwargs|
        captured = kwargs
        { "choices" => [ { "message" => { "content" => llm_json_payload(payload) } } ] }
      end

      described_class.call(job: job)

      user_msg = captured[:messages].find { |m| m[:role] == "user" }[:content]
      expect(user_msg).to include("roleword")
      expect(user_msg).to include("trait_big_five")
      job.reload
      expect(job.wsi_jd_big_five_profile["input_source"]).to eq("lia_enriched")
    end

    it "falls back to job description when approved but enriched yields no text" do
      job = create(
        :job,
        description: ("fallback " * 60).strip,
        lia_job_description: { "status" => "approved", "enriched_jd" => {} }
      )
      payload = uniform_traits(score: 45, evidence: [ '"x"' ])
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => llm_json_payload(payload) } } ]
      )

      described_class.call(job: job)

      job.reload
      expect(job.wsi_jd_big_five_profile["input_source"]).to eq("job_description")
    end

    it "returns error when input text is blank" do
      job = create(:job, description: "", responsibilities: nil)
      allow(client).to receive(:chat)
      result = described_class.call(job: job)

      expect(result[:success]).to be false
      expect(result[:code]).to eq("wsi_jd_input_missing")
      expect(client).not_to have_received(:chat)
    end

    it "returns error when LLM content is empty" do
      job = create(:job, description: ("word " * 60).strip)
      allow(client).to receive(:chat).and_return("choices" => [ { "message" => { "content" => "" } } ])

      result = described_class.call(job: job)

      expect(result[:success]).to be false
      expect(result[:code]).to eq("wsi_llm_empty")
    end

    it "returns error when JSON missing big_five_jd" do
      job = create(:job, description: ("word " * 60).strip)
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => { other: 1 }.to_json } } ]
      )

      result = described_class.call(job: job)

      expect(result[:success]).to be false
      expect(result[:code]).to eq("wsi_jd_big_five_parse_error")
    end

    it "parses JSON when the model wraps it in a markdown code fence" do
      job = create(:job, description: ("word " * 60).strip)
      inner = uniform_traits(score: 50, evidence: [ '"trecho"' ])
      wrapped = "```json\n#{llm_json_payload(inner)}\n```"
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => wrapped } } ]
      )

      result = described_class.call(job: job)

      expect(result[:success]).to be true
      expect(job.reload.wsi_jd_big_five_profile["big_five_jd"]).to be_present
    end

    it "accepts neuroticism key from model mapped into stability bucket" do
      job = create(:job, description: ("word " * 60).strip)
      rows = uniform_traits(score: 50, evidence: [ '"a"' ])
      rows.delete("stability")
      rows["neuroticism"] = { "score" => 40, "evidence" => [ '"n"' ], "confidence" => "medium" }
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => llm_json_payload(rows) } } ]
      )

      result = described_class.call(job: job)

      expect(result[:success]).to be true
      expect(job.reload.wsi_jd_big_five_profile["big_five_jd"]["stability"]["score"]).to eq(40)
    end

    context "evidence and JD length rules" do
      it "marks jd_insufficient and forces low confidence when under 50 useful words" do
        job = create(:job, description: "one two three four five six seven eight nine ten")
        payload = uniform_traits(score: 80, evidence: [ '"lots"' ], confidence: "high")
        allow(client).to receive(:chat).and_return(
          "choices" => [ { "message" => { "content" => llm_json_payload(payload) } } ]
        )

        described_class.call(job: job)

        profile = job.reload.wsi_jd_big_five_profile
        expect(profile["jd_insufficient"]).to be true
        note = Wsi::JdBigFiveExtractionService::JD_INSUFFICIENT_NOTE
        profile["big_five_jd"].each_value do |row|
          expect(row["confidence"]).to eq("low")
          expect(row["evidence"]).to eq([ note ])
        end
      end

      it "truncates evidence strings and keeps at most four items per trait" do
        job = create(:job, description: ("word " * 60).strip)
        long = "a" * 250
        six_items = (1..6).map { |i| "item #{i} " + ("b" * 30) }
        payload = uniform_traits(score: 55, evidence: six_items + [ long ])
        allow(client).to receive(:chat).and_return(
          "choices" => [ { "message" => { "content" => llm_json_payload(payload) } } ]
        )

        described_class.call(job: job)

        row = job.reload.wsi_jd_big_five_profile["big_five_jd"]["openness"]
        expect(row["evidence"].size).to eq(described_class::MAX_EVIDENCE_ITEMS_PER_TRAIT)
        expect(row["evidence"].map(&:length).max).to be <= described_class::MAX_EVIDENCE_STRING_CHARS
      end

      it "sets _evidence_missing and clamps score when evidence empty" do
        job = create(:job, description: ("word " * 60).strip)
        payload = uniform_traits(score: 80, evidence: [])
        allow(client).to receive(:chat).and_return(
          "choices" => [ { "message" => { "content" => llm_json_payload(payload) } } ]
        )

        described_class.call(job: job)

        row = job.reload.wsi_jd_big_five_profile["big_five_jd"]["openness"]
        expect(row["_evidence_missing"]).to be true
        expect(row["confidence"]).to eq("low")
        expect(row["score"]).to eq(30)
      end
    end
  end
end
