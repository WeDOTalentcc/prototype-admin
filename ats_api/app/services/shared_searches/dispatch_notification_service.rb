module SharedSearches
  class DispatchNotificationService
    def self.call(shared_search, emails: nil)
      new(shared_search, emails: emails).call
    end

    def initialize(shared_search, emails: nil)
      @shared_search = shared_search
      @emails = Array(emails).presence || shared_search.shared_with_emails
    end

    def call
      return [] if @emails.blank?

      @emails.map do |email|
        enqueue_email(email)
        email
      end
    end

    private

    def enqueue_email(email)
      Rails.logger.info(
        "[SharedSearches] Queued notification shared_search_id=#{@shared_search.id} to=#{email}"
      )
    end
  end
end
