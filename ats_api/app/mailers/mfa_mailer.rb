# frozen_string_literal: true

class MfaMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")

  def otp_email
    @user = params[:user]
    @account = @user.account
    @code = params[:code]
    @expires_in = "5 minutos"
    @front_url = ENV["FRONT_URL"] || "http://localhost:3000"
    @company_name = @account&.name || "WeDO Talent"

    mail(
      to: @user.email,
      subject: "Seu código de verificação - WeDO Talent"
    )
  end
end
