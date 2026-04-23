# frozen_string_literal: true

module V1
  module Evaluations
    class MessagesController < ApplicationController
      include RenderDefault

      def index
        messages = Message
          .where(reference_type: "EvaluationCandidate", reference_id: @evaluation_candidate.id)
          .order(created_at: :asc)
          .limit(params[:limit] || 100)

        render json: {
          data: messages.map { |m|
            {
              id: m.id,
              content: m.content,
              entity: m.entity,
              status: m.status,
              metadata: m.metadata,
              created_at: m.created_at.iso8601
            }
          },
          meta: { total: messages.size }
        }, status: :ok
      end

      def create
        @message = Message.new(message_params.merge(
          reference: @evaluation_candidate,
          account_id: @account.id,
          entity: message_params[:entity] || Message::ROLE_USER,
          status: Message::STATUS_NOT_ANSWERED
        ))

        if @message.save
          return render_success(@message, serializer: MessageSerializer, status: :created)
        end
        render_error(@message, status: :unprocessable_entity)
      end

      private

      def message_params
        params.require(:message).permit(
          :content, :entity, :domain,
          metadata: [ :question_id, voice_message: [ :base64, :mime_type, :duration ] ]
        )
      end
    end
  end
end
