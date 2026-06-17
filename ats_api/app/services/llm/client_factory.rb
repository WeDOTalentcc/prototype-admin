# frozen_string_literal: true

module Llm
  class ClientFactory
    DEFAULT_PROVIDER = "gemini"

    ADAPTER_MAP = {
      "gemini" => Llm::Adapters::Gemini,
      "openai" => Llm::Adapters::Openai,
      "anthropic" => Llm::Adapters::Anthropic,
      "deepseek" => Llm::Adapters::Deepseek
    }.freeze

    def self.build(account: nil)
      account ||= Current.user&.account || Current.account
      config = resolve_configuration(account)

      adapter_class = ADAPTER_MAP.fetch(config[:provider], Llm::Adapters::Gemini)
      adapter_class.new(api_key: config[:api_key])
    end

    def self.build_for_embeddings(account: nil)
      account ||= Current.user&.account || Current.account
      config = resolve_configuration(account)

      return default_gemini_adapter if LlmConfiguration::EMBEDDING_PROVIDERS.exclude?(config[:provider])

      adapter_class = ADAPTER_MAP.fetch(config[:provider], Llm::Adapters::Gemini)
      adapter_class.new(api_key: config[:api_key])
    end

    def self.chat_model(account: nil)
      account ||= Current.user&.account || Current.account
      config = resolve_configuration(account)
      LlmConfiguration::PROVIDER_DEFAULTS.dig(config[:provider], :chat_model) ||
        ENV.fetch("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
    end

    def self.fast_model(account: nil)
      account ||= Current.user&.account || Current.account
      config = resolve_configuration(account)
      LlmConfiguration::PROVIDER_DEFAULTS.dig(config[:provider], :chat_model) ||
        ENV.fetch("GEMINI_FAST_MODEL", "gemini-2.5-flash")
    end

    def self.embedding_model(account: nil)
      account ||= Current.user&.account || Current.account
      config = resolve_configuration(account)
      LlmConfiguration::PROVIDER_DEFAULTS.dig(config[:provider], :embedding_model) ||
        ENV.fetch("EMBEDDING_MODEL", "gemini-embedding-001")
    end

    def self.resolve_configuration(account)
      return default_configuration unless account

      llm_config = Apartment::Tenant.switch("public") { account.llm_configuration }

      return default_configuration unless llm_config&.active?

      api_key = llm_config.api_key
      return default_configuration if api_key.blank?

      unless plausible_api_key?(api_key)
        Rails.logger.warn(
          "[Llm::ClientFactory] account_id=#{account.id} llm_configuration.api_key rejeitada (placeholder); caindo no ENV default"
        )
        return default_configuration
      end

      { provider: llm_config.provider, api_key: api_key }
    end

    # Placeholders como "123123123123" vieram do seed de dev e fariam o Gemini
    # retornar 400 em toda embedding. Chaves reais (Gemini/OpenAI/Anthropic)
    # têm length ≥ 20 e sempre incluem letras — seed lixo é só dígito.
    def self.plausible_api_key?(api_key)
      key = api_key.to_s
      key.length >= 20 && !key.match?(/\A\d+\z/)
    end

    def self.default_configuration
      { provider: DEFAULT_PROVIDER, api_key: ENV.fetch("GOOGLE_API_KEY") }
    end

    def self.default_gemini_adapter
      Llm::Adapters::Gemini.new(api_key: ENV.fetch("GOOGLE_API_KEY"))
    end

    private_class_method :resolve_configuration, :plausible_api_key?, :default_configuration, :default_gemini_adapter
  end
end
