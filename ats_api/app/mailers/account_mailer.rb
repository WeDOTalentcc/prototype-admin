class AccountMailer < ApplicationMailer
  default from: ENV["MAILGUN_EMAIL"] || "noreply@example.com"

  layout false

  def signup_email(to:, account_name:, setup_url:, content:)
    @account_name = account_name
    @setup_url = setup_url
    @content = content

    mail(
      to: to,
      subject: "Bem-vindo ao #{account_name}! Complete seu cadastro"
    )
  end
end
