# frozen_string_literal: true

module Jobs
  class RefreshAnalyticsJob
    include Sidekiq::Job

    sidekiq_options queue: :low, retry: 2

    DEBOUNCE_TTL = 30
    LOCK_PREFIX = "job_analytics_refresh"

    def self.enqueue(job_id, account_id)
      lock_key = "#{LOCK_PREFIX}:#{job_id}"

      locked = Sidekiq.redis { |conn| conn.set(lock_key, "1", nx: true, ex: DEBOUNCE_TTL) }
      return unless locked

      perform_in(DEBOUNCE_TTL, job_id, account_id)
    end

    def perform(job_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        job = Job.find_by(id: job_id)
        return unless job

        ::Jobs::AnalyticsService.new(job: job, force_refresh: true).call
      end
    rescue StandardError => e
      Rails.logger.error "[Jobs::RefreshAnalyticsJob] Error for Job##{job_id}: #{e.message}"
      raise
    ensure
      Sidekiq.redis { |conn| conn.del("#{LOCK_PREFIX}:#{job_id}") }
    end
  end
end
