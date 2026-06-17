module V1
  module Users
    class AudioMessagesController < ApplicationController
      def create
        message = Message.create!(
          content: audio_message_params[:transcription] || "[Audio message]",
          reference_type: "User",
          reference_id: @current_user.id,
          entity: Message::ROLE_USER,
          status: Message::STATUS_NOT_ANSWERED,
          account_id: @current_user.account_id,
          metadata: {
            is_audio: true,
            audio_format: audio_message_params[:audio_format] || "wav",
            audio_duration: audio_message_params[:audio_duration]
          }
        )

        audio_payload = {
          original_message_id: message.id,
          user_reference_type: "User",
          user_reference_id: @current_user.id,
          account_id: @current_user.account_id,
          audio_data: audio_message_params[:audio_data],
          audio_format: audio_message_params[:audio_format] || "wav"
        }

        publish_audio_message(audio_payload)

        render_success({
          message: "Audio message received and being processed",
          message_id: message.id
        }, status: :accepted)
      rescue => e
        render_error({ message: "Error processing audio message: #{e.message}" }, status: :unprocessable_entity)
      end

      def show
        message = Message.find_by(id: params[:id], reference_id: @current_user.id)
        return render_not_found("Message") unless message

        render_success({
          id: message.id,
          content: message.content,
          entity: message.entity,
          status: message.status,
          metadata: message.metadata,
          created_at: message.created_at
        })
      end

      def audio
        message = Message.find_by(id: params[:id])
        return render_not_found("Message") unless message
        return head(:not_found) unless message.audio_file.attached?

        redirect_to rails_blob_url(message.audio_file, disposition: "inline")
      end

      private

      def audio_message_params
        params.require(:audio_message).permit(:audio_data, :audio_format, :audio_duration, :transcription)
      end

      def publish_audio_message(payload)
        MessageService::EventPublisher.publish(
          payload,
          exchange_name: "messages_exchange",
          routing_key: "audio_messages_created"
        )
      end
    end
  end
end
