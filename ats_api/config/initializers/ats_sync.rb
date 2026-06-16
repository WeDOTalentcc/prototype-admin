# frozen_string_literal: true

module AtsSync
  class Configuration
    attr_accessor :enabled, :api_url, :api_token, :timeout, :retry_attempts

    def initialize
      @enabled = ENV.fetch("ATS_SYNC_ENABLED", "true") == "true"
      @api_url = ENV.fetch("DATA_COLLECTOR_URL", "http://localhost:8001")
      @api_token = ENV.fetch("DATA_COLLECTOR_TOKEN", "")
      @timeout = ENV.fetch("ATS_SYNC_TIMEOUT", "30").to_i
      @retry_attempts = ENV.fetch("ATS_SYNC_RETRY_ATTEMPTS", "3").to_i
    end

    def enabled?
      @enabled && @api_token.present?
    end
  end

  class << self
    def config
      @config ||= Configuration.new
    end

    def configure
      yield(config)
    end
  end
end
