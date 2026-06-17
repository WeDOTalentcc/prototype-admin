class ApplicationMailer < ActionMailer::Base
  default from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")
  layout "mailer"
end
