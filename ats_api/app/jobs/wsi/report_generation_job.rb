# frozen_string_literal: true

module Wsi
  class ReportGenerationJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform(evaluation_candidate_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        ec = EvaluationCandidate.find_by(id: evaluation_candidate_id)
        return unless ec

        result = Wsi::ReportBuilderService.call(evaluation_candidate: ec, persist: true)
        unless result[:success]
          Rails.logger.warn("⚠️ [ReportGenerationJob] ec=#{evaluation_candidate_id} #{result[:error]}")
        end
      end
    rescue StandardError => e
      Rails.logger.error("❌ [ReportGenerationJob] #{e.class} #{e.message}")
      raise
    end
  end
end
