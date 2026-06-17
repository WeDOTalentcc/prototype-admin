# frozen_string_literal: true

class LlmConfiguration < ApplicationRecord
  PROVIDERS = {
    gemini: 0,
    openai: 1,
    anthropic: 2,
    deepseek: 3
  }.freeze

  VALID_PROVIDERS = PROVIDERS.keys.map(&:to_s).freeze

  PROVIDER_LABELS = {
    "gemini" => "Google Gemini",
    "openai" => "OpenAI (ChatGPT)",
    "anthropic" => "Anthropic (Claude)",
    "deepseek" => "DeepSeek"
  }.freeze

  PROVIDER_DEFAULTS = {
    "gemini" => { chat_model: "gemini-2.5-flash", embedding_model: "gemini-embedding-001" },
    "openai" => { chat_model: "gpt-4o-mini", embedding_model: "text-embedding-3-small" },
    "anthropic" => { chat_model: "claude-sonnet-4-20250514", embedding_model: nil },
    "deepseek" => { chat_model: "deepseek-chat", embedding_model: nil }
  }.freeze

  EMBEDDING_PROVIDERS = %w[gemini openai].freeze

  belongs_to :account

  validates :account_id, uniqueness: true
  validates :encrypted_api_key, presence: true
  validates :encrypted_provider, presence: true
  validate :provider_must_be_valid

  def provider=(value)
    @provider_cache = value.to_s
    self.encrypted_provider = self.class.encrypt_value(@provider_cache)
  end

  def provider
    @provider_cache ||= self.class.decrypt_value(encrypted_provider)
  end

  def api_key=(value)
    self.encrypted_api_key = self.class.encrypt_value(value)
  end

  def api_key
    return nil if encrypted_api_key.blank?

    self.class.decrypt_value(encrypted_api_key)
  end

  def masked_api_key
    return nil if encrypted_api_key.blank?

    raw = api_key
    return nil if raw.blank?
    return "****" if raw.length < 12

    "#{raw[0..2]}#{"*" * [raw.length - 6, 6].max}#{raw[-3..]}"
  end

  def provider_label
    PROVIDER_LABELS[provider] || provider&.titleize
  end

  def supports_embeddings?
    EMBEDDING_PROVIDERS.include?(provider)
  end

  def default_chat_model
    PROVIDER_DEFAULTS.dig(provider, :chat_model)
  end

  def default_embedding_model
    PROVIDER_DEFAULTS.dig(provider, :embedding_model)
  end

  def self.encrypt_value(value)
    return nil if value.blank?

    encryptor.encrypt_and_sign(value)
  end

  def self.decrypt_value(encrypted_value)
    return nil if encrypted_value.blank?

    encryptor.decrypt_and_verify(encrypted_value)
  rescue ActiveSupport::MessageEncryptor::InvalidMessage, ActiveSupport::MessageVerifier::InvalidSignature
    Rails.logger.error "[LlmConfiguration] Failed to decrypt value"
    nil
  end

  def self.encryptor
    @encryptor ||= begin
      secret = Rails.application.secret_key_base
      key = ActiveSupport::KeyGenerator.new(secret).generate_key("llm_configuration_encryption", 32)
      ActiveSupport::MessageEncryptor.new(key)
    end
  end

  private

  def provider_must_be_valid
    return if provider.blank?

    errors.add(:provider, "is not a valid provider") unless VALID_PROVIDERS.include?(provider)
  end
end
