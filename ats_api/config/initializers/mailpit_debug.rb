# Log SMTP config em development para verificar se Mailpit está sendo usado
if Rails.env.development?
  Rails.application.config.after_initialize do
    settings = ActionMailer::Base.smtp_settings
    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Rails.logger.info "📧 [Mailpit] SMTP config: #{settings[:address]}:#{settings[:port]}"
    Rails.logger.info "   Mailpit Web UI: http://localhost:8025" if settings[:address].to_s.include?("mailpit") || settings[:port] == 1025
    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end
end
