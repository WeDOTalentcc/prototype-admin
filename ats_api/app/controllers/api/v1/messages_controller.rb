# frozen_string_literal: true

module Api
  module V1
    class MessagesController < ApplicationController
      before_action :authenticate_internal_api

      def create
        resolve_workspace_for_domain
        message = build_message
        return render_validation_error(message) unless message.save

        message.workspace&.update_last_message!
        render_success(message)
      rescue => e
        log_error(e)
        render_internal_error(e)
      end

      private

      def build_message
        message = Message.new(message_params)
        message.no_reply = ActiveModel::Type::Boolean.new.cast(params[:message][:no_reply]) if params[:message][:no_reply].present?

        if params.dig(:message, :audio_file).present?
          message.audio_file.attach(params[:message][:audio_file])
          message.content_format = "audio"
          message.content = "🎤 Mensagem de voz" if message.content.blank?
        end

        message
      end

      def resolve_workspace_for_domain
        domain = message_param(:domain)
        domain_reference_id = extract_domain_reference_id
        return if domain.blank? || domain_reference_id.blank? || message_param(:workspace_id).present?

        user = User.find_by(id: message_param(:reference_id))
        return unless user

        workspace = Workspace.find_or_create_for_domain(user: user, account: user.account, domain: domain, domain_reference_id: domain_reference_id)
        params[:message][:workspace_id] = workspace&.id
      end

      def extract_domain_reference_id
        message_param(:domain_reference_id) || params[:domain_reference_id] || extract_from_metadata
      end

      def extract_from_metadata
        metadata = message_param(:metadata)
        return unless metadata.is_a?(Hash) || metadata.is_a?(ActionController::Parameters)

        metadata[:sourcing_id] || metadata["sourcing_id"] || metadata[:domain_reference_id] || metadata["domain_reference_id"]
      end

      def message_param(key)
        params.dig(:message, key)
      end

      def message_params
        params.require(:message).permit(
          :reference_type, :reference_id, :account_id, :workspace_id,
          :entity, :content, :content_format, :status, :domain,
          :audio_file,
          metadata: {}
        )
      end

      def authenticate_internal_api
        return if valid_api_secret?

        Rails.logger.warn("Unauthorized API access attempt from IP: #{request.remote_ip}")
        render json: { error: "Unauthorized", message: "Invalid or missing X-Internal-API-Secret header" }, status: :unauthorized
      end

      def valid_api_secret?
        secret = request.headers["X-Internal-API-Secret"]
        expected = ENV["INTERNAL_API_SECRET"]
        secret.present? && expected.present? && secret == expected
      end

      def render_success(message)
        render json: { status: "ok", message_id: message.id, workspace_id: message.workspace_id, message: "Message created successfully" }, status: :created
      end

      def render_validation_error(message)
        render json: { error: "Failed to create message", details: message.errors.full_messages }, status: :unprocessable_entity
      end

      def render_internal_error(error)
        render json: { error: "Internal server error", message: error.message }, status: :internal_server_error
      end

      def log_error(error)
        Rails.logger.error("Error creating message from Python: #{error.class} #{error.message}")
        Rails.logger.error(error.backtrace.join("\n"))
      end
    end
  end
end
