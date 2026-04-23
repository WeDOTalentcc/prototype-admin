# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::FeedbackAnalyzerService do
  let(:service) { described_class.new(llm_client: llm_client) }
  let(:llm_client) { instance_double(GeminiClient) }

  let(:base_candidates) do
    [
      build(:candidate, name: "João Silva", role_name: "Senior Ruby Developer", current_company: "Tech Corp"),
      build(:candidate, name: "Maria Santos", role_name: "Backend Engineer", current_company: "StartupX")
    ]
  end

  let(:liked_candidates) do
    [
      build(:candidate, name: "Ana Costa", role_name: "Tech Lead Ruby", current_company: "iFood")
    ]
  end

  let(:dislike_feedbacks) do
    [
      {
        candidate: build(:candidate, name: "Pedro Junior", role_name: "Junior Developer", current_company: "SmallCo"),
        reason: "too junior, only 2 years of experience"
      },
      {
        candidate: build(:candidate, name: "Carlos Lima", role_name: "Developer", current_company: "RetailCo"),
        reason: "wrong industry, need fintech experience"
      }
    ]
  end

  describe "#analyze" do
    context "when there are 2+ dislikes with reasons" do
      let(:llm_response) do
        {
          "choices" => [
            {
              "message" => {
                "content" => {
                  "desired_profile" => "Senior developer with 5+ years experience in fintech",
                  "rejection_patterns" => [ "junior developers", "non-fintech companies" ],
                  "positive_patterns" => [ "senior level", "tech leadership experience" ],
                  "explanation" => "Recruiter values seniority and fintech domain expertise"
                }.to_json
              }
            }
          ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it "returns analysis from LLM" do
        result = service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislike_feedbacks
        )

        expect(result).to be_a(Hash)
        expect(result[:desired_profile]).to eq("Senior developer with 5+ years experience in fintech")
        expect(result[:rejection_patterns]).to include("junior developers", "non-fintech companies")
        expect(result[:positive_patterns]).to include("senior level", "tech leadership experience")
        expect(result[:explanation]).to be_present
      end

      it "sends correct prompt to LLM" do
        service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislike_feedbacks
        )

        expect(llm_client).to have_received(:chat) do |args|
          messages = args[:messages]
          expect(messages.size).to eq(2)
          expect(messages[0][:role]).to eq("system")
          expect(messages[1][:role]).to eq("user")
          expect(messages[1][:content]).to include("João Silva")
          expect(messages[1][:content]).to include("Ana Costa")
          expect(messages[1][:content]).to include("too junior")
          expect(messages[1][:content]).to include("wrong industry")
        end
      end
    end

    context "when there is only 1 dislike" do
      let(:single_dislike) do
        [
          {
            candidate: build(:candidate, name: "Pedro Junior"),
            reason: "too junior"
          }
        ]
      end

      before do
        allow(llm_client).to receive(:chat)
      end

      it "returns nil without calling LLM" do
        result = service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: single_dislike
        )

        expect(result).to be_nil
        expect(llm_client).not_to have_received(:chat)
      end
    end

    context "when there are no dislikes" do
      before do
        allow(llm_client).to receive(:chat)
      end

      it "returns nil without calling LLM" do
        result = service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: []
        )

        expect(result).to be_nil
        expect(llm_client).not_to have_received(:chat)
      end
    end

    context "when LLM call times out" do
      before do
        allow(llm_client).to receive(:chat).and_raise(Timeout::Error)
      end

      it "returns nil gracefully" do
        result = service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislike_feedbacks
        )

        expect(result).to be_nil
      end

      it "logs warning" do
        expect(Rails.logger).to receive(:warn).with(/LLM timeout/)

        service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislike_feedbacks
        )
      end
    end

    context "when LLM returns invalid JSON" do
      before do
        allow(llm_client).to receive(:chat).and_return(
          {
            "choices" => [
              {
                "message" => {
                  "content" => "This is not valid JSON"
                }
              }
            ]
          }
        )
      end

      it "returns nil gracefully" do
        result = service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislike_feedbacks
        )

        expect(result).to be_nil
      end

      it "logs warning" do
        expect(Rails.logger).to receive(:warn).with(/JSON parse failed/)

        service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislike_feedbacks
        )
      end
    end

    context "when LLM returns JSON with markdown backticks" do
      let(:llm_response) do
        {
          "choices" => [
            {
              "message" => {
                "content" => "```json\n{\"desired_profile\":\"Senior dev\",\"rejection_patterns\":[],\"positive_patterns\":[],\"explanation\":\"test\"}\n```"
              }
            }
          ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it "strips markdown and parses JSON correctly" do
        result = service.analyze(
          base_candidates: base_candidates,
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislike_feedbacks
        )

        expect(result).to be_a(Hash)
        expect(result[:desired_profile]).to eq("Senior dev")
      end
    end
  end
end
