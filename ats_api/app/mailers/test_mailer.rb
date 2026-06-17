class TestMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")

  def hello_email(to)
    mail(
      to: to,
      subject: "Teste Mailgun 🚀",
      body: "Olá, este é um teste de envio via Mailgun configurado no Rails!"
    )
  end
end
