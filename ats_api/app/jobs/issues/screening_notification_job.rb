# frozen_string_literal: true

module Issues
  class ScreeningNotificationJob < ApplicationJob
    queue_as :default

    def perform(issue_id, account_id)
      return unless issue_id.present? && account_id.present?

      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      issue = Issue.find_by(id: issue_id)
      return unless issue

      IssueMailer.screening_notification(issue).deliver_now

      Rails.logger.info "✅ [Issues::ScreeningNotificationJob] E-mail de screening enviado para issue ##{issue_id}"
    rescue StandardError => e
      Rails.logger.error "❌ [Issues::ScreeningNotificationJob] Falha: #{e.class} - #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise
    end
  end
end
