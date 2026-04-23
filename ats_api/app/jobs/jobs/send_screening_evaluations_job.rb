# frozen_string_literal: true

module Jobs
  class SendScreeningEvaluationsJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    LOCK_PREFIX = "job_screening_send"
    LOCK_TTL = 120

    def perform(job_id, account_id)
      lock_key = "#{LOCK_PREFIX}:#{job_id}"
      locked = Sidekiq.redis { |conn| conn.set(lock_key, "1", nx: true, ex: LOCK_TTL) }
      unless locked
        Rails.logger.info "⏭️ [SendScreeningEvaluationsJob] SKIP job_id=#{job_id} (already running)"
        return
      end

      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        result = Jobs::SendScreeningEvaluationsService.call(job_id: job_id, account_id: account_id)

        if result[:success]
          Rails.logger.info "✅ [SendScreeningEvaluationsJob] Sent=#{result[:sent_count]} Skipped=#{result[:skipped_saturation]}"
        else
          Rails.logger.warn "⏸️  [SendScreeningEvaluationsJob] #{result[:error]}"
        end
      end
    rescue StandardError => e
      Rails.logger.error "❌ [SendScreeningEvaluationsJob] job_id=#{job_id} #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise
    ensure
      Sidekiq.redis { |conn| conn.del("#{LOCK_PREFIX}:#{job_id}") }
    end
  end
end
