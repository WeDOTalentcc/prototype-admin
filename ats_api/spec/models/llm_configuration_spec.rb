# frozen_string_literal: true

RSpec.describe LlmConfiguration do
  subject(:config) { build(:llm_configuration) }

  describe "validations" do
    it { is_expected.to be_valid }

    it "requires provider" do
      config.encrypted_provider = nil
      expect(config).not_to be_valid
    end

    it "rejects invalid provider" do
      config.provider = "invalid_provider"
      expect(config).not_to be_valid
    end

    it "requires encrypted_api_key" do
      config.encrypted_api_key = nil
      expect(config).not_to be_valid
    end

    it "enforces uniqueness per account" do
      create(:llm_configuration, account: config.account)
      expect(config).not_to be_valid
    end
  end

  describe "provider encryption" do
    it "encrypts the provider on assignment" do
      config.provider = "openai"
      expect(config.encrypted_provider).not_to eq("openai")
      expect(config.encrypted_provider).to be_present
    end

    it "decrypts the provider on read" do
      config.provider = "anthropic"
      expect(config.provider).to eq("anthropic")
    end

    it "produces different ciphertext each time" do
      config.provider = "gemini"
      first = config.encrypted_provider
      config.provider = "gemini"
      second = config.encrypted_provider
      expect(first).not_to eq(second)
    end

    it "round-trips through save" do
      config.provider = "deepseek"
      config.save!
      reloaded = described_class.find(config.id)
      expect(reloaded.provider).to eq("deepseek")
    end
  end

  describe "api_key encryption" do
    it "encrypts the api_key on assignment" do
      config.api_key = "sk-test-12345"
      expect(config.encrypted_api_key).not_to eq("sk-test-12345")
      expect(config.encrypted_api_key).to be_present
    end

    it "decrypts the api_key on read" do
      config.api_key = "sk-test-12345"
      expect(config.api_key).to eq("sk-test-12345")
    end

    it "produces different ciphertext each time" do
      config.api_key = "sk-same-key"
      first = config.encrypted_api_key
      config.api_key = "sk-same-key"
      second = config.encrypted_api_key
      expect(first).not_to eq(second)
    end

    it "round-trips through save" do
      config.api_key = "sk-round-trip-test"
      config.save!
      reloaded = described_class.find(config.id)
      expect(reloaded.api_key).to eq("sk-round-trip-test")
    end
  end

  describe "#masked_api_key" do
    it "masks the middle of the key" do
      config.api_key = "sk-1234567890abcdef"
      masked = config.masked_api_key
      expect(masked).to start_with("sk-1")
      expect(masked).to end_with("cdef")
      expect(masked).to include("*")
      expect(masked).not_to eq("sk-1234567890abcdef")
    end

    it "returns nil when no key" do
      config.encrypted_api_key = nil
      expect(config.masked_api_key).to be_nil
    end

    it "returns **** for short keys" do
      config.api_key = "short"
      expect(config.masked_api_key).to eq("****")
    end
  end

  describe "#provider_label" do
    it "returns human-readable label for gemini" do
      config.provider = "gemini"
      expect(config.provider_label).to eq("Google Gemini")
    end

    it "returns human-readable label for openai" do
      config.provider = "openai"
      expect(config.provider_label).to eq("OpenAI (ChatGPT)")
    end

    it "returns human-readable label for anthropic" do
      config.provider = "anthropic"
      expect(config.provider_label).to eq("Anthropic (Claude)")
    end

    it "returns human-readable label for deepseek" do
      config.provider = "deepseek"
      expect(config.provider_label).to eq("DeepSeek")
    end
  end

  describe "#supports_embeddings?" do
    it "returns true for gemini" do
      config.provider = "gemini"
      expect(config.supports_embeddings?).to be true
    end

    it "returns true for openai" do
      config.provider = "openai"
      expect(config.supports_embeddings?).to be true
    end

    it "returns false for anthropic" do
      config.provider = "anthropic"
      expect(config.supports_embeddings?).to be false
    end

    it "returns false for deepseek" do
      config.provider = "deepseek"
      expect(config.supports_embeddings?).to be false
    end
  end
end
