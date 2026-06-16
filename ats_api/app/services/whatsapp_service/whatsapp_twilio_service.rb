require "twilio-ruby"

module WhatsappService
  class WhatsappTwilioService
    attr_reader :client

    def initialize
      account_sid = ENV["TWILIO_ACCOUNT_SID"]
      auth_token = ENV["TWILIO_AUTH_TOKEN"]
      @from_number = ENV["TWILIO_WHATSAPP_NUMBER"] # Carrega o número aqui

      # Validação robusta para todas as credenciais necessárias
      unless account_sid && auth_token && @from_number
        raise "Twilio credentials not found. Make sure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER are set in your .env file."
      end

      @client = Twilio::REST::Client.new(account_sid, auth_token)
    end

    def send_templated_message(to:, content_sid:, variables:)
      # Agora usamos a variável de instância que já foi validada
      formatted_to = "whatsapp:#{to}"
      formatted_from = "whatsapp:#{@from_number}"

      begin
        message = client.messages.create(
          from: formatted_from,
          to: formatted_to,
          content_sid: content_sid,
          content_variables: variables.to_json
        )

        # Usamos o logger do Rails que é mais apropriado
        Rails.logger.info "WhatsApp message sent successfully to #{to}. SID: #{message.sid}"
        { success: true, sid: message.sid }
      rescue Twilio::REST::RestError => e
        Rails.logger.error "Error sending WhatsApp message to #{to}: #{e.message}"
        { success: false, error: e.message }
      end
    end
  end
end
