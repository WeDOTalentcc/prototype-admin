# frozen_string_literal: true

RSpec.describe Llm::ClientFactory do
  let(:account) { create(:account) }

  describe ".build" do
    context "when account has no llm_configuration" do
      it "returns a Gemini adapter with default ENV key" do
        client = described_class.build(account: account)
        expect(client).to be_a(Llm::Adapters::Gemini)
      end
    end

    context "when account has active gemini configuration" do
      before { create(:llm_configuration, account: account, provider: "gemini", api_key: "custom-key-123") }

      it "returns a Gemini adapter with account-specific key" do
        client = described_class.build(account: account)
        expect(client).to be_a(Llm::Adapters::Gemini)
        expect(client.api_key).to eq("custom-key-123")
      end
    end

    context "when account has active openai configuration" do
      before { create(:llm_configuration, account: account, provider: "openai", api_key: "sk-openai-key") }

      it "returns an OpenAI adapter" do
        client = described_class.build(account: account)
        expect(client).to be_a(Llm::Adapters::Openai)
        expect(client.api_key).to eq("sk-openai-key")
      end
    end

    context "when account has active anthropic configuration" do
      before { create(:llm_configuration, account: account, provider: "anthropic", api_key: "sk-ant-key") }

      it "returns an Anthropic adapter" do
        client = described_class.build(account: account)
        expect(client).to be_a(Llm::Adapters::Anthropic)
      end
    end

    context "when account has active deepseek configuration" do
      before { create(:llm_configuration, account: account, provider: "deepseek", api_key: "sk-deep-key") }

      it "returns a DeepSeek adapter" do
        client = described_class.build(account: account)
        expect(client).to be_a(Llm::Adapters::Deepseek)
      end
    end

    context "when account has inactive llm_configuration" do
      before { create(:llm_configuration, :inactive, account: account, api_key: "inactive-key") }

      it "falls back to default Gemini adapter" do
        client = described_class.build(account: account)
        expect(client).to be_a(Llm::Adapters::Gemini)
      end
    end

    context "when account is nil" do
      it "returns a Gemini adapter with default ENV key" do
        client = described_class.build(account: nil)
        expect(client).to be_a(Llm::Adapters::Gemini)
      end
    end
  end

  describe ".build_for_embeddings" do
    context "when account uses openai (supports embeddings)" do
      before { create(:llm_configuration, account: account, provider: "openai", api_key: "sk-openai") }

      it "returns an OpenAI adapter" do
        client = described_class.build_for_embeddings(account: account)
        expect(client).to be_a(Llm::Adapters::Openai)
      end
    end

    context "when account uses anthropic (no embedding support)" do
      before { create(:llm_configuration, account: account, provider: "anthropic", api_key: "sk-ant") }

      it "falls back to default Gemini adapter" do
        client = described_class.build_for_embeddings(account: account)
        expect(client).to be_a(Llm::Adapters::Gemini)
      end
    end

    context "when account uses deepseek (no embedding support)" do
      before { create(:llm_configuration, account: account, provider: "deepseek", api_key: "sk-deep") }

      it "falls back to default Gemini adapter" do
        client = described_class.build_for_embeddings(account: account)
        expect(client).to be_a(Llm::Adapters::Gemini)
      end
    end
  end
end
