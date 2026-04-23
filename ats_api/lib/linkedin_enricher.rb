class LinkedinEnricher
  class << self
    def enrich(candidate_or_id)
      candidate = candidate_or_id.is_a?(Candidate) ? candidate_or_id : Candidate.find(candidate_or_id)

      Rails.logger.info "[LinkedinEnricher] Enriching candidate #{candidate.id} - #{candidate.name}"

      service = Candidates::LinkedinEnrichmentService.new(candidate)
      result = service.call

      if result.success?
        Rails.logger.info "[LinkedinEnricher] Successfully enriched candidate #{candidate.id}"
      else
        Rails.logger.error "[LinkedinEnricher] Failed to enrich candidate #{candidate.id}: #{result.error}"
      end

      result
    end

    def enrich_by_linkedin(linkedin_url_or_username)
      candidate = find_candidate_by_linkedin(linkedin_url_or_username)
      return nil unless candidate

      enrich(candidate.id)
    end

    def fetch_payload(linkedin_url_or_username)
      username = extract_username(linkedin_url_or_username)
      return nil unless username

      Rails.logger.info "[LinkedinEnricher] Fetching Apify data for username: #{username}"

      results = Apify::LinkedinProfileParserService.parse(
        linkedin_profile_urls: [ username ],
        include_email: true
      )

      payload = results.first

      unless payload && !payload[:error]
        Rails.logger.error "[LinkedinEnricher] Error fetching data: #{payload[:error]}"
      end

      payload
    end

    private

    def find_candidate_by_linkedin(linkedin_url_or_username)
      Candidate.where("linkedin ILIKE ?", "%#{linkedin_url_or_username}%").first
    end

    def extract_username(url_or_username)
      return nil unless LinkedinUrlValidator.valid?(url_or_username)
      LinkedinUrlParser.extract_username(url_or_username) || url_or_username
    end
  end
end
