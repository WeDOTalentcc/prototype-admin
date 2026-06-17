require "exception_notification/rails"

# Configurar exception_notification apenas em production
if Rails.env.production?
  ExceptionNotification.configure do |config|
    # Ignorar alguns erros comuns que não precisam de notificação
    config.ignore_if do |exception, options|
      not_found_exceptions = [
        "ActionController::RoutingError",
        "ActiveRecord::RecordNotFound",
        "ActionController::InvalidAuthenticityToken",
        "ActionController::UnknownFormat"
      ]

      not_found_exceptions.include?(exception.class.name)
    end

  # Configuração para envio por email
  config.add_notifier :email, {
    email_prefix: "[ATS ERROR] ",
    sender_address: %("ATS Error" <#{ENV['MAILGUN_EMAIL'] || 'noreply@example.com'}>),
    exception_recipients: ENV.fetch("EXCEPTION_NOTIFICATION_EMAILS", "").split(",").map(&:strip),

    # Configurações SMTP usando Mailgun
    delivery_method: :smtp,
    smtp_settings: {
      address: ENV["MAILGUN_HOST"] || "smtp.mailgun.org",
      port: ENV["MAILGUN_PORT"] || 587,
      domain: ENV["domain_name"] || "localhost",
      user_name: ENV["MAILGUN_EMAIL"],
      password: ENV["MAILGUN_PASS"],
      authentication: :plain,
      enable_starttls_auto: true
    },

    # Informações adicionais no email
    email_headers: {
      "X-ATS-Environment" => Rails.env,
      "X-ATS-Server" => ENV["APP_HOST"] || "localhost"
    },

    # Seções incluídas no email de erro
    sections: %w[request session environment backtrace],

    # Incluir dados sensíveis filtrados
    background_sections: %w[backtrace data],

    # Verbose para debug (apenas em development)
    verbose_subject: true,

    # Normalizar assunto do email
    normalize_subject: true,

    # Incluir silent exceptions (que não renderizam)
    deliver_with: :deliver_now
  }
  end
end
