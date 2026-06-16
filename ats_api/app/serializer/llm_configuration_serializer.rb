# frozen_string_literal: true

class LlmConfigurationSerializer
  include JSONAPI::Serializer

  attributes :provider, :active, :created_at, :updated_at,
             :interview_ai_synced_at, :interview_ai_sync_error

  attribute :masked_api_key, &:masked_api_key

  attribute :provider_label, &:provider_label

  attribute :supports_embeddings, &:supports_embeddings?

  attribute :default_chat_model, &:default_chat_model

  attribute :default_embedding_model, &:default_embedding_model

  attribute :interview_ai_synced do |config|
    config.interview_ai_synced_at.present? && config.interview_ai_sync_error.blank?
  end
end
