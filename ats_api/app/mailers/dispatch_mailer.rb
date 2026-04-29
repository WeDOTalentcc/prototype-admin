class DispatchMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")

  def dispatch_email
    @message = params[:message]
    @account_name = @message&.account&.name || "WeDO Talent"
    @front_url = front_url

    mail(
      to: @message.recipient_address,
      subject: @message.subject
    )
  end

  def send_email(to:, subject:, body:, from: nil)
    @body = body

    mail(
      to: to,
      subject: subject,
      from: from || ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")
    ) do |format|
      format.html { render inline: @body }
    end
  end

  private

  def front_url
    ENV.fetch("FRONT_URL", "https://app.wedotalent.cc")
  end
end
