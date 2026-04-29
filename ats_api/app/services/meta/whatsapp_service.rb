module Meta
  class WhatsappService
    RETRY_DELAYS = [ 0, 30.seconds, 2.minutes ].freeze
    MAX_ATTEMPTS = 3

    # Proteção contra envio acidental em dev/staging.
    # ENV:
    #   WHATSAPP_ALLOW_SEND - "true" para permitir envios em não-produção (override)
    #   WHATSAPP_ALLOWED_PHONES - números permitidos em dev (vírgula). Ex: "+5511999999999,5511888888888"
    class << self
      def send_text_message(phone_number, message)
        params = {
          messaging_product: "whatsapp",
          to: phone_number,
          type: "text",
          text: { body: message }
        }
        send_with_retry(params)
      end

      def send_message_by_template(phone_number, template, language = "pt_BR", components)
        params = {
          messaging_product: "whatsapp",
          to: phone_number,
          type: "template",
          template: {
            name: template,
            language: { code: language },
            components: components
          }
        }
        send_with_retry(params)
      end

      def send_link(phone:, body_text:, url:, button_text: "Acessar link")
        payload = {
          messaging_product: "whatsapp",
          to: phone,
          type: "interactive",
          interactive: {
            type: "cta_url",
            body: { text: body_text },
            action: {
              name: "cta_url",
              parameters: {
                display_text: button_text,
                url: url
              }
            }
          }
        }
        send_with_retry(payload)
      end

      def send_allowed?(phone)
        return true if Rails.env.production?

        return true if ENV["WHATSAPP_ALLOW_SEND"]&.downcase == "true"

        allowed = ENV["WHATSAPP_ALLOWED_PHONES"]&.split(",")&.map { |p| normalize_phone(p) }&.compact

        return false if allowed.blank?

        allowed.include?(normalize_phone(phone.to_s))
      end

      private

      def send_with_retry(params)
        unless send_allowed?(params[:to])
          Rails.logger.info "📵 [WhatsApp] Envio bloqueado (dev/staging) para #{params[:to]} - use WHATSAPP_ALLOW_SEND ou WHATSAPP_ALLOWED_PHONES"
          return Meta::Api::Response.new(202, { "messages" => [ { "id" => "dev-blocked-#{SecureRandom.hex(8)}" } ] }, nil, true)
        end

        last_error = nil

        MAX_ATTEMPTS.times do |attempt|
          sleep(RETRY_DELAYS[attempt]) if attempt > 0

          response = Meta::Api.post("messages", params)
          return response if response.success?

          last_error = response.body
        end

        Meta::Api::Response.new(0, last_error || {}, nil, false)
      end

      def normalize_phone(phone)
        phone.to_s.gsub(/\D/, "").presence
      end
    end
  end
end
