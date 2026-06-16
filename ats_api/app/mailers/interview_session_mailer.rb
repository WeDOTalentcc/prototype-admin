# frozen_string_literal: true

class InterviewSessionMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")

  layout false

  def invite(session)
    @session = session
    @candidate = session.candidate
    @interview_url = session.public_url
    @job_title = session.job_context["title"]
    @company_name = session.account.name
    @duration = session.duration_minutes
    @expires_at = session.expires_at

    mail(
      to: @candidate.email,
      subject: "Voice Interview Invitation - #{@job_title}"
    )
  end

  def completed(session)
    @session = session
    @recruiter = session.created_by
    @candidate_name = session.candidate_context["name"]
    @job_title = session.job_context["title"]
    @score = session.score
    @recommendation = session.recommendation

    mail(
      to: @recruiter.email,
      subject: "Interview Completed: #{@candidate_name} - #{@job_title}"
    )
  end
end
