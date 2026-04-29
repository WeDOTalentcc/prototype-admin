# frozen_string_literal: true

module Jobs
  class SendScreeningEvaluationsCronJob
    include Sidekiq::Job

    sidekiq_options queue: :low, retry: 2

    def perform
      enqueued = 0

      Account.find_each do |account|
        next if account.tenant.blank?

        Apartment::Tenant.switch(account.tenant) do
          job_ids = Job.where(is_screening_active: true, is_deleted: false)
            .within_screening_send_window
            .pluck(:id)

          job_ids.each do |job_id|
            Jobs::SendScreeningEvaluationsJob.perform_async(job_id, account.id)
            enqueued += 1
          end
        end
      rescue ActiveRecord::StatementInvalid => e
        next if e.message.include?("is_screening_active") && e.message.include?("does not exist")
        raise
      end

      Rails.logger.info "✅ [SendScreeningEvaluationsCronJob] Enqueued #{enqueued} jobs"
    rescue StandardError => e
      Rails.logger.error "❌ [SendScreeningEvaluationsCronJob] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise
    end
  end
end
