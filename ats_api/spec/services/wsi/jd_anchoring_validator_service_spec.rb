# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::JdAnchoringValidatorService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) do
    create(
      :job,
      user: user,
      account: account,
      title: "Backend",
      description: "Construir APIs REST em Ruby e integrar com PostgreSQL.",
      lia_job_description: {}
    )
  end

  it "parses anchored JSON from Gemini" do
    client = instance_double(GeminiClient)
    allow(GeminiClient).to receive(:new).and_return(client)
    allow(client).to receive(:chat).and_return(
      "choices" => [
        {
          "message" => {
            "content" => {
              is_anchored: true,
              evidence_in_jd: '"APIs REST"',
              anchor_type: "skill",
              confidence: "high",
              anchor_explanation: "A pergunta cita o stack do JD.",
              suggestion: ""
            }.to_json
          }
        }
      ]
    )

    result = described_class.call(
      job: job,
      question_text: "Descreva como você projetou APIs REST com Ruby.",
      skill_or_trait_label: "Ruby",
      question_category: "technical"
    )

    expect(result.success?).to be true
    expect(result.data[:is_anchored]).to be true
    expect(result.data[:anchor_type]).to eq("skill")
  end
end
