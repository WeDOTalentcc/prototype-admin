# frozen_string_literal: true

class SchedulingMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "noreply@example.com")

  layout false

  def booking_confirmed_recruiter(user:, meeting:, link:)
    @user = user
    @meeting = meeting
    @link = link
    @candidate = link.candidate

    mail(
      to: user.email,
      subject: "Interview Booked: #{meeting.subject}"
    )
  end

  def booking_confirmed_candidate(candidate:, meeting:, link:)
    @candidate = candidate
    @meeting = meeting
    @link = link

    mail(
      to: candidate.email,
      subject: "Your interview has been scheduled: #{meeting.subject}"
    )
  end

  def scheduling_invite(candidate:, link:, user:, account:)
    @candidate = candidate
    @link = link
    @user = user
    @scheduling_url = build_scheduling_url(account.uid, link.token)

    mail(
      to: candidate.email,
      subject: link.subject.presence || "Choose your interview time"
    )
  end

  private

  def build_scheduling_url(account_uid, token)
    frontend = ENV.fetch("FRONT_URL", "http://localhost:3000")
    "#{frontend}/scheduling/#{account_uid}/#{token}"
  end
end
