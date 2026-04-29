# frozen_string_literal: true

module Candidates
  class LinkedinEnrichmentService
    Result = Struct.new(:success?, :stats, :error, keyword_init: true)

    attr_reader :candidate

    def initialize(candidate)
      @candidate = candidate
    end

    def call
      return failure_result("LinkedIn URL não informada") if candidate.linkedin.blank?
      return failure_result("URL do LinkedIn inválida") unless valid_linkedin_url?

      linkedin_data = fetch_linkedin_data
      return failure_result("Dados não encontrados no LinkedIn") if linkedin_data.blank?
      return failure_result(linkedin_data[:error]) if linkedin_data[:error]

      stats = process_linkedin_data(linkedin_data)
      success_result(stats)
    rescue Apify::LinkedinProfileParserService::RateLimitError => e
      failure_result("Rate limit do LinkedIn atingido. Tentando novamente em #{e.minutes_until_retry} minutos")
    rescue => e
      Rails.logger.error "[LinkedinEnrichmentService] Error: #{e.message}"
      failure_result("Erro ao enriquecer perfil: #{e.message}")
    end

    private

    def valid_linkedin_url?
      LinkedinUrlValidator.valid?(candidate.linkedin)
    end

    def fetch_linkedin_data
      username = LinkedinUrlParser.extract_username(candidate.linkedin)
      return nil unless username

      results = Apify::LinkedinProfileParserService.parse(
        linkedin_profile_urls: [ username ],
        include_email: true
      )

      results.first
    end

    def process_linkedin_data(linkedin_data)
      candidate.update!(
        data_raw: linkedin_data.deep_stringify_keys,
        linkedin_enriched_at: Time.current
      )

      processor = LinkedinDataProcessor.new(candidate, linkedin_data)
      processor.process_all
    end

    def success_result(stats)
      Result.new(success?: true, stats: stats, error: nil)
    end

    def failure_result(error_message)
      Result.new(success?: false, stats: {}, error: error_message)
    end
  end
end
