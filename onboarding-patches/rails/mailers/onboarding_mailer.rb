# frozen_string_literal: true

class OnboardingMailer < ApplicationMailer
  default from: "LIA <lia@wedotalent.com>"

  # Welcome email with magic link + WhatsApp CTA
  def welcome_email(user:, magic_link_url:, admin_name:, whatsapp_number: nil)
    @user = user
    @magic_link_url = magic_link_url
    @admin_name = admin_name
    @whatsapp_url = whatsapp_number ? "https://wa.me/#{whatsapp_number}?text=#{CGI.escape("Oi LIA, sou #{user.name}")}" : nil
    @company_name = user.account&.name || "WeDOTalent"

    mail(
      to: user.email,
      subject: "Oi #{user.name}! Sou a LIA, sua nova colega de recrutamento"
    )

    # Track email send
    EmailLog.create(
      user_id: user.id,
      template_name: "onboarding_welcome",
      recipient_email: user.email,
      subject: "Oi #{user.name}! Sou a LIA",
      status: "sent",
      sent_at: Time.current
    ) rescue nil
  end
end
