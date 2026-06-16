class PasswordResetMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")

  layout false

  def reset_password_email
    @user = params[:user]
    @token = params[:token]
    @reset_url = params[:reset_url]

    mail(
      to: @user.email,
      subject: "Redefinição de senha - We Do Talent"
    )
  end

  def new_access_email
    @user = params[:user]
    @token = params[:token]
    @reset_url = params[:reset_url]

    mail(
      to: @user.email,
      subject: "Novo acesso criado - We Do Talent"
    )
  end
end
