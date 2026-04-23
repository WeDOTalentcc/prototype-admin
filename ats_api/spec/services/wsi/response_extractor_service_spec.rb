# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::ResponseExtractorService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:question) do
    create(
      :question,
      evaluation: evaluation,
      competence_type: "technical",
      bloom_level: "analyze",
      dreyfus_target: 4,
      wsi_metadata: { "expected_signals" => %w[ownership metrics] }
    )
  end
  let(:answer) do
    create(
      :answer,
      question: question,
      evaluation: evaluation,
      candidate: candidate,
      user: user,
      account: account,
      job: job,
      description: "Eu implementei cache e reduzi latência em 40%."
    )
  end

  let(:fixture_json) do
    {
      star_components: { situation: true, task: true, action: true, result: true },
      trait_signals_detected: [],
      trait_signals_absent: [],
      bloom_demonstrated: 3,
      bloom_label: "Aplicar",
      dreyfus_demonstrated: 3,
      dreyfus_label: "Competent",
      inflation_detected: false,
      inflation_evidence: "",
      specificity_score: 7,
      key_quote: "\"reduzi latência\"",
      response_authentic: true,
      authenticity_concern: nil
    }.to_json
  end

  describe ".call" do
    it "invokes Gemini with temperature 0 and parses JSON" do
      client = instance_double(GeminiClient)
      allow(GeminiClient).to receive(:new).and_return(client)
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => fixture_json } } ]
      )

      result = described_class.call(answer: answer, masked_response_text: answer.description)

      expect(client).to have_received(:chat).with(
        hash_including(temperature: 0.0, max_tokens: 800)
      )
      expect(result.success?).to be true
      expect(result.data[:bloom_demonstrated]).to eq(3)
      expect(result.data[:specificity_score]).to eq(7)
      expect(result.data[:trait_signals_detected].size).to eq(1)
      expect(result.data[:trait_signals_backfilled]).to be true
      expect(result.data[:trait_signals_detected].first).to include("Technical evidence")
    end

    it "coerces null trait_signals from LLM to empty arrays when answer is not substantive" do
      payload = JSON.parse(fixture_json)
      payload["trait_signals_detected"] = nil
      payload["trait_signals_absent"] = nil
      payload["authenticity_concern"] = "response_too_short"
      payload["specificity_score"] = 2
      client = instance_double(GeminiClient)
      allow(GeminiClient).to receive(:new).and_return(client)
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => payload.to_json } } ]
      )

      result = described_class.call(answer: answer, masked_response_text: "short")

      expect(result.data[:trait_signals_detected]).to eq([])
      expect(result.data[:trait_signals_absent]).to eq([])
      expect(result.data[:trait_signals_backfilled]).to be_nil
    end

    it "backfills behavioral label when question is behavioral" do
      question.update!(competence_type: "behavioral", ocean_trait: "conscientiousness")
      payload = JSON.parse(fixture_json)
      payload["trait_signals_detected"] = []
      client = instance_double(GeminiClient)
      allow(GeminiClient).to receive(:new).and_return(client)
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => payload.to_json } } ]
      )

      result = described_class.call(answer: answer, masked_response_text: answer.description)

      expect(result.data[:trait_signals_detected].first).to include("Behavioral evidence")
    end

    it "returns conservative fallback when content is empty" do
      client = instance_double(GeminiClient)
      allow(GeminiClient).to receive(:new).and_return(client)
      allow(client).to receive(:chat).and_return(
        "choices" => [ { "message" => { "content" => "" } } ]
      )

      result = described_class.call(answer: answer, masked_response_text: "x")
      expect(result.data[:_llm_fallback]).to be true
    end
  end
end
