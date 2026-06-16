# frozen_string_literal: true

class IssueMailer < ApplicationMailer
  SCREENING_NOTIFICATION_EMAIL = "felipe.augusto@wedotalent.cc".freeze

  default from: ENV["MAILGUN_EMAIL"] || "noreply@wedotalent.cc"

  layout false

  def screening_notification(issue)
    @issue = issue
    @content = issue.text
    @candidate_name = issue.candidate&.name
    @mobile_phone = issue.candidate&.mobile_phone
    @email = issue.candidate&.email
    @issue_date = issue.created_at
    @job_name = issue.job&.title || "Não informada"

    mail(
      to: screening_notification_recipients,
      subject: "[Screening] Problema reportado por #{@candidate_name} - #{@job_name}"
    )
  end

  private

  def screening_notification_recipients
    if Rails.env.production?
      %w[felipe.augusto@wedotalent.cc anderson.victhor@wedotalent.cc]
    else
      SCREENING_NOTIFICATION_EMAIL
    end
  end
end
