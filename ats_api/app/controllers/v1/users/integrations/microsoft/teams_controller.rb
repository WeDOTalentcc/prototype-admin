# frozen_string_literal: true

require "cgi"

module V1
  module Users
    module Integrations
      module Microsoft
        class TeamsController < V1::Users::ApplicationController
          include MicrosoftLinked

          def message
            raw = message_params

            if raw[:team].is_a?(ActionController::Parameters) || raw[:team].is_a?(Hash)
              nested = raw[:team].to_h.symbolize_keys
              raw = raw.to_h.symbolize_keys.merge(nested)
              raw.delete(:team)
            end
            message_attributes = raw.symbolize_keys
            Rails.logger.info({ event: "teams.message.start", to: message_attributes[:to], chat_id: message_attributes[:chat_id], team_name: message_attributes[:team_name], channel_name: message_attributes[:channel_name], team_id: message_attributes[:team_id], channel_id: message_attributes[:channel_id] }.to_json)
            begin
              result = MicrosoftService::Teams.send_message(
                user: @current_user,
                content: message_attributes[:content],
                content_type: message_attributes[:content_type],
                chat_id: message_attributes[:chat_id],
                to: message_attributes[:to],
                team_id: message_attributes[:team_id],
                channel_id: message_attributes[:channel_id],
                team_name: message_attributes[:team_name],
                channel_name: message_attributes[:channel_name]
              )
              render json: { ok: true, id: result[:message_id] }, status: :accepted
            rescue MicrosoftService::Teams::Error => e
              Rails.logger.warn({ event: "teams.message.fail", code: e.code, message: e.message }.to_json)
              render json: { error: e.message, reason: e.code }, status: :unprocessable_entity
            end
          rescue => error
            Rails.logger.error("MS Teams message error: #{error.class} #{error.message}")
            Rails.logger.error(error.backtrace&.first(5)&.join("\n"))
            render json: { error: "Falha ao enviar mensagem no Teams" }, status: :unprocessable_entity
          end

          private

          def message_params
            params.permit(
              :chat_id, :team_id, :channel_id, :content, :content_type, :to, :team_name, :channel_name,
              team: [ :chat_id, :team_id, :channel_id, :content, :content_type, :to, :team_name, :channel_name ]
            )
          end

          # Resolução agora está em MicrosoftService::Teams
        end
      end
    end
  end
end
