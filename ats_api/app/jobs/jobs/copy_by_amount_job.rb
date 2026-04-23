# frozen_string_literal: true

module Jobs
  class CopyByAmountJob < ApplicationJob
    queue_as :critical
    sidekiq_options retry: 2

    def perform(amount, job_id, user_id, entities = [])
      user = User.find_by(id: user_id)
      return unless user&.account

      Apartment::Tenant.switch(user.account.tenant) do
        Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        Rails.logger.info("🚀 [CopyByAmountJob] Starting job duplication")
        Rails.logger.info("   Tenant: #{user.account.tenant}, Amount: #{amount}, Job ID: #{job_id}, User: #{user_id}")
        Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        ::Jobs::CopyService.copy_multiple(
          amount: amount,
          job_id: job_id,
          user_id: user_id,
          entities: entities
        )

        Rails.logger.info("✅ [CopyByAmountJob] Job duplication completed")
      end
    rescue => e
      Rails.logger.error("❌ [CopyByAmountJob] Failed: #{e.message}")
      Rails.logger.error(e.backtrace.first(10).join("\n"))
      raise
    end
  end
end
