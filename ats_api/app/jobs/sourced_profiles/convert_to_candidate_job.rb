# frozen_string_literal: true

module SourcedProfiles
  class ConvertToCandidateJob < ApplicationJob
    queue_as :default

    def perform(sourced_profile_ids, account_id = nil)
      Apartment::Tenant.switch!(tenant_name(account_id)) if account_id

      result = SourcedProfiles::ConvertToCandidateService.call(sourced_profile_ids)

      log_result(result)
    rescue => e
      Rails.logger.error("SourcedProfiles::ConvertToCandidateJob failed: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
      raise
    end

    private

    def tenant_name(account_id)
      return "public" unless account_id

      Account.find(account_id).tenant
    end

    def log_result(result)
      Rails.logger.info("=== SourcedProfile to Candidate Conversion Summary ===")
      Rails.logger.info("Converted: #{result[:converted]}")
      Rails.logger.info("Skipped: #{result[:skipped]}")
      Rails.logger.info("Failed: #{result[:failed]}")

      if result[:errors].any?
        Rails.logger.error("Conversion errors:")
        result[:errors].each do |error|
          Rails.logger.error("  SourcedProfile #{error[:sourced_profile_id]}: #{error[:error]}")
        end
      end
    end
  end
end
