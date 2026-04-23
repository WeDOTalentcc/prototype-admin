# frozen_string_literal: true

class RejectFeedbackMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "noreply@wedotalent.cc")

  layout false

  def feedback_to_candidate(candidate:, feedback:, job:)
    @candidate = candidate
    @feedback = feedback
    @job = job
    @feedback_description = feedback.description

    subject = feedback.title.presence || "Atualização sobre sua candidatura - #{job.title}"
    mail(to: candidate.email, subject: subject)
  end
end
