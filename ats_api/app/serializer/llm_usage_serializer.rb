# frozen_string_literal: true

class LlmUsageSerializer
  include JSONAPI::Serializer

  attributes :id, :model, :operation, :input_tokens, :output_tokens,
             :total_tokens, :success, :error_message, :context, :user_id,
             :account_id, :created_at

  attribute :cost_usd do |object|
    object.cost_usd.to_f.round(8)
  end

  attribute :latency_ms do |object|
    object.latency_ms.to_f.round(2)
  end

  attribute :user_name do |object|
    object.user&.name
  end

  attribute :user_email do |object|
    object.user&.email
  end

  attribute :service_name do |object|
    object.context&.dig("service")
  end
end
