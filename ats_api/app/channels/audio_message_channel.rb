# frozen_string_literal: true

class AudioMessageChannel < ApplicationCable::Channel
  def receive(data)
    handle_audio_message(data) if data["type"] == "audio_message"
  end

  private

  def after_authentication
    stream_from "audio_messages_user_#{current_user.id}"
  end

  def handle_audio_message(data)
    return unless current_user

    begin
      message = Message.create!(
        content: data["transcription"] || "[Mensagem de áudio]",
        reference_type: "User",
        reference_id: current_user.id,
        entity: Message::ROLE_USER,
        status: Message::STATUS_NOT_ANSWERED,
        account_id: current_user.account_id,
        metadata: {
          is_audio: true,
          audio_format: data["audio_format"] || "wav",
          audio_duration: data["audio_duration"]
        }
      )

      audio_payload = {
        original_message_id: message.id,
        user_reference_type: "User",
        user_reference_id: current_user.id,
        audio_data: data["audio_data"],
        audio_format: data["audio_format"] || "wav"
      }

      connection_rabbit = Bunny.new(ENV.fetch("RABBITMQ_URL"))
      connection_rabbit.start

      begin
        channel_rabbit = connection_rabbit.create_channel
        exchange = channel_rabbit.direct("messages_exchange", durable: true)

        exchange.publish(
          audio_payload.to_json,
          routing_key: "audio_messages_created",
          persistent: true,
          headers: {
            message_type: "audio_message",
            user_id: current_user.id,
            message_id: message.id
          }
        )
      ensure
        connection_rabbit.close
      end

      data_file = DataFile.find_by(reference_type: "Message", reference_id: message.id, account_id: current_user.account_id)
      public_url = nil
      if data_file&.uid && current_user.account&.uid
        public_url = "/v1/data_file/#{current_user.account.uid}/#{data_file.uid}"
      end

      transmit({
        type: "audio_received",
        message_id: message.id,
        status: "processing",
        public_url: public_url
      })
    rescue StandardError => e
      Rails.logger.error "❌ [AudioMessageChannel] #{e.message}"
      transmit({
        type: "error",
        message: "Erro ao processar mensagem de áudio"
      })
    end
  end
end
