# frozen_string_literal: true

module V1
  module Users
    class MessagesController < ApplicationController
      before_action :authorize_request
      before_action :set_message, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        search_with_pin[:where].merge!(reference_id: @current_user.id, reference_type: "User")
        perform_search(
          model: Message,
          serializer: MessageSerializer,
        )
      end

      def show
        render_success(@message, serializer: MessageSerializer)
      end

      def create
        message_params_data = set_message_params
        message_params_data[:workspace_id] = resolve_valid_workspace_id(message_params_data)

        @message = Message.new(message_params_data)
        attach_audio_if_present

        return render_error(@message, status: :unprocessable_entity) unless @message.save

        update_workspace_last_message
        render_success(@message, serializer: MessageSerializer, status: :created)
      end

      def update
        return render_error(@message) unless @message.update(set_message_params)

        render_success(@message, serializer: MessageSerializer)
      end

      def destroy
        @message.destroy
        head :no_content
      end

      private

      def set_message
        @message = Message.find_by(id: params[:id])
        return if @message

        render json: { error: "Message not found" }, status: :not_found
      end

      def ensure_owner
        return if @message.reference_id == @current_user.id && @message.reference_type == "User"

        render json: { error: "Not authorized" }, status: :forbidden
      end

      def set_message_params
        current_message_params = message_params.except(:file_urls, :domain_reference_id)
        current_message_params[:reference_type] = "User"
        current_message_params[:reference_id] = @current_user.id
        current_message_params[:content_format] ||= "plain_text"
        current_message_params
      end

      def resolve_valid_workspace_id(message_params_data)
        workspace_id = message_params_data[:workspace_id]

        if workspace_id.present? && workspace_id.to_i > 0
          return workspace_id if Workspace.active.exists?(id: workspace_id)
        end

        workspace = find_workspace_from_parent_message || resolve_workspace(message_params_data)
        workspace.id
      end

      def find_workspace_from_parent_message
        parent_id = params[:message_id] || params.dig(:message, :parent_message_id)
        return if parent_id.blank?

        parent_message = Message.find_by(id: parent_id)
        return if parent_message.blank?

        return Workspace.active.find_by(id: parent_message.workspace_id) if parent_message.workspace_id.present?

        find_teams_workspace_from_metadata(parent_message)
      end

      def find_teams_workspace_from_metadata(message)
        metadata = message.metadata
        return unless metadata.is_a?(Hash)

        teams_chat_id = metadata["teams_chat_id"] || metadata[:teams_chat_id]
        return if teams_chat_id.blank?

        Workspace.active.find_by(
          user_id: @current_user.id,
          domain: "teams",
          domain_reference_id: teams_chat_id
        )
      end

      def resolve_workspace(message_params_data)
        domain = message_params_data[:domain]
        domain_reference_id = extract_domain_reference_id(message_params_data)

        if domain.blank? || (domain_reference_id.blank? && !Workspace.singleton_domain?(domain))
          return create_default_workspace(message_params_data[:content])
        end

        Workspace.find_or_create_for_domain(
          user: @current_user,
          account: @current_user.account,
          domain: domain,
          domain_reference_id: domain_reference_id
        )
      end

      def extract_domain_reference_id(message_params_data)
        return message_params[:domain_reference_id] if message_params[:domain_reference_id].present?

        metadata = message_params_data[:metadata]
        return nil unless metadata.is_a?(Hash) || metadata.is_a?(ActionController::Parameters)

        metadata[:sourcing_id] || metadata["sourcing_id"] ||
          metadata[:domain_reference_id] || metadata["domain_reference_id"]
      end

      def create_default_workspace(content)
        workspace = Workspace.create(user: @current_user, account: @current_user.account)
        workspace.generate_fields(content)
        workspace
      end

      def attach_audio_if_present
        return unless params.dig(:message, :audio_file).present?

        @message.audio_file.attach(params[:message][:audio_file])
        @message.content_format = "audio"
        @message.content = "🎤 Mensagem de voz" if @message.content.blank?
      end

      def update_workspace_last_message
        return if @message.workspace_id.blank?

        workspace = Workspace.find_by(id: @message.workspace_id)
        return unless workspace&.user_id == @current_user.id && workspace.has_messages?

        workspace.update_last_message!
      end

      def message_params
        params.require(:message).permit(
          :content, :content_format, :user_context_id, :type, :is_deleted,
          :status, :parent_message_id, :reference_type, :reference_id,
          :entity, :workspace_id, :no_reply, :domain, :domain_reference_id,
          :audio_file, :is_thinking, :thinking_status,
          data_file_ids: [], file_urls: [], metadata: {}, execution_tracking: {}
        )
      end
    end
  end
end
