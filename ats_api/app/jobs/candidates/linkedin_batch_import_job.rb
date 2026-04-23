# frozen_string_literal: true

module Candidates
  class LinkedinBatchImportJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform(account_id, job_id, selective_process_id, linkedin_urls, user_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        job = Job.find_by(id: job_id)
        selective_process = SelectiveProcess.find_by(id: selective_process_id, is_deleted: false)
        user = User.find_by(id: user_id)

        unless job && selective_process && user
          Rails.logger.error "❌ [LinkedinBatchImportJob] Missing records - Job: #{job_id}, SP: #{selective_process_id}, User: #{user_id}"
          return
        end

        Current.user = user
        Current.account = account

        Candidates::LinkedinBatchImportService.new(
          job: job,
          selective_process: selective_process,
          linkedin_urls: linkedin_urls,
          account: account,
          user: user
        ).call
      end
    rescue StandardError => e
      Rails.logger.error "❌ [LinkedinBatchImportJob] #{e.message}"
      raise
    end
  end
end
