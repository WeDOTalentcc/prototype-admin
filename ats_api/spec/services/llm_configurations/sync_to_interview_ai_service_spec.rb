# frozen_string_literal: true

require "rails_helper"
require "webmock/rspec"

RSpec.describe LlmConfigurations::SyncToInterviewAiService do
  subject(:result) { described_class.new(llm_configuration: llm_configuration).call }

  let(:account) { create(:account) }
  let(:llm_configuration) { create(:llm_configuration, account: account) }

  let(:base_url) { "http://interview-ai-test:8001" }
  let(:secret_token) { "test-secret-token" }

  before do
    allow(ENV).to receive(:fetch).and_call_original
    allow(ENV).to receive(:fetch).with("INTERVIEW_AI_BASE_URL", nil).and_return(base_url)
    allow(ENV).to receive(:fetch).with("LLM_CONFIG_SECRET", nil).and_return(secret_token)
  end

  context "when sync succeeds" do
    before do
      stub_request(:put, "#{base_url}/api/v1/llm/configurations")
        .with(
          headers: { "Authorization" => "Bearer #{secret_token}" }
        )
        .to_return(status: 200, body: { success: true }.to_json, headers: { "Content-Type" => "application/json" })
    end

    it "returns success" do
      expect(result[:success]).to be true
    end

    it "updates interview_ai_synced_at" do
      freeze_time do
        result
        expect(llm_configuration.reload.interview_ai_synced_at).to eq(Time.current)
      end
    end

    it "clears interview_ai_sync_error" do
      llm_configuration.update_columns(interview_ai_sync_error: "previous error")
      result
      expect(llm_configuration.reload.interview_ai_sync_error).to be_nil
    end
  end

  context "when interview-ai returns error" do
    before do
      stub_request(:put, "#{base_url}/api/v1/llm/configurations")
        .to_return(status: 500, body: "Internal Server Error")
    end

    it "returns failure" do
      expect(result[:success]).to be false
    end

    it "records the error" do
      result
      expect(llm_configuration.reload.interview_ai_sync_error).to include("HTTP 500")
    end
  end

  context "when connection times out" do
    before do
      stub_request(:put, "#{base_url}/api/v1/llm/configurations")
        .to_timeout
    end

    it "returns failure" do
      expect(result[:success]).to be false
    end

    it "records timeout error" do
      result
      expect(llm_configuration.reload.interview_ai_sync_error).to include("Connection failed")
    end
  end

  context "when connection fails" do
    before do
      stub_request(:put, "#{base_url}/api/v1/llm/configurations")
        .to_raise(Faraday::ConnectionFailed.new("Connection refused"))
    end

    it "returns failure with connection error" do
      expect(result[:success]).to be false
      expect(result[:error]).to include("Connection failed")
    end
  end

  context "when INTERVIEW_AI_BASE_URL is not configured" do
    let(:base_url) { nil }

    it "returns failure" do
      expect(result[:success]).to be false
      expect(result[:error]).to include("INTERVIEW_AI_BASE_URL not configured")
    end
  end

  context "when LLM_CONFIG_SECRET is not configured" do
    let(:secret_token) { nil }

    it "returns failure" do
      expect(result[:success]).to be false
      expect(result[:error]).to include("LLM_CONFIG_SECRET not configured")
    end
  end

  context "when sending request body" do
    before do
      stub_request(:put, "#{base_url}/api/v1/llm/configurations")
        .with(
          body: hash_including(
            "account_id" => llm_configuration.account_id,
            "provider" => llm_configuration.provider
          )
        )
        .to_return(status: 200, body: { success: true }.to_json, headers: { "Content-Type" => "application/json" })
    end

    it "sends account_id and provider in body" do
      expect(result[:success]).to be true
    end
  end
end
