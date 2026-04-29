# frozen_string_literal: true

module V1
  module Users
    class LlmConfigurationsController < ApplicationController
      before_action :set_llm_configuration, only: %i[show update destroy retry_sync]
      before_action :authorize_admin!, only: %i[create update destroy retry_sync]

      def show
        render_success(@llm_configuration, serializer: LlmConfigurationSerializer)
      end

      def create
        existing = LlmConfiguration.find_by(account_id: @current_user.account_id)
        return update_existing(existing) if existing

        config = LlmConfiguration.new(llm_configuration_params)
        config.account_id = @current_user.account_id
        config.api_key = params.dig(:llm_configuration, :api_key)

        return render_error(config, status: :unprocessable_entity) unless config.save

        sync_to_interview_ai(config)
        render_success(config, serializer: LlmConfigurationSerializer, status: :created)
      end

      def update
        @llm_configuration.api_key = params.dig(:llm_configuration, :api_key) if params.dig(:llm_configuration, :api_key).present?

        return render_error(@llm_configuration, status: :unprocessable_entity) unless @llm_configuration.update(llm_configuration_params)

        sync_to_interview_ai(@llm_configuration)
        render_success(@llm_configuration, serializer: LlmConfigurationSerializer)
      end

      def destroy
        @llm_configuration.destroy
        head :no_content
      end

      def status
        config = LlmConfiguration.find_by(account_id: @current_user.account_id)
        return render json: { configured: false }, status: :ok unless config

        render json: {
          configured: true,
          id: config.id,
          provider: config.provider,
          provider_label: config.provider_label,
          active: config.active,
          interview_ai_synced: config.interview_ai_synced_at.present? && config.interview_ai_sync_error.blank?,
          interview_ai_synced_at: config.interview_ai_synced_at,
          interview_ai_sync_error: config.interview_ai_sync_error,
          created_at: config.created_at,
          updated_at: config.updated_at
        }, status: :ok
      end

      def retry_sync
        result = LlmConfigurations::SyncToInterviewAiService.new(llm_configuration: @llm_configuration).call

        return render_success(@llm_configuration, serializer: LlmConfigurationSerializer) if result[:success]

        render json: { error: result[:error], synced: false }, status: :unprocessable_entity
      end

      def providers
        providers = LlmConfiguration::PROVIDER_LABELS.map do |key, label|
          {
            id: key,
            name: label,
            supports_embeddings: LlmConfiguration::EMBEDDING_PROVIDERS.include?(key),
            default_chat_model: LlmConfiguration::PROVIDER_DEFAULTS.dig(key, :chat_model),
            default_embedding_model: LlmConfiguration::PROVIDER_DEFAULTS.dig(key, :embedding_model)
          }
        end

        render json: { providers: providers }
      end

      private

      def set_llm_configuration
        @llm_configuration = LlmConfiguration.find_by(account_id: @current_user.account_id)
        render_not_found("LlmConfiguration") unless @llm_configuration
      end

      def update_existing(config)
        config.api_key = params.dig(:llm_configuration, :api_key) if params.dig(:llm_configuration, :api_key).present?

        return render_error(config, status: :unprocessable_entity) unless config.update(llm_configuration_params)

        sync_to_interview_ai(config)
        render_success(config, serializer: LlmConfigurationSerializer)
      end

      def llm_configuration_params
        params.require(:llm_configuration).permit(:provider, :active)
      end

      def sync_to_interview_ai(config)
        LlmConfigurations::SyncToInterviewAiService.new(llm_configuration: config).call
      end

      def authorize_admin!
        return if @current_user&.has_role?("admin") || @current_user&.has_role?("super_admin")

        render_simple_error("Only admins can manage LLM configurations", status: :forbidden)
      end
    end
  end
end
