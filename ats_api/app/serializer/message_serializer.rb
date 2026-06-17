class MessageSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :content,
    :content_format,
    :entity,
    :is_deleted,
    :status,
    :parent_message_id,
    :reference_type,
    :reference_id,
    :account_id,
    :created_at,
    :updated_at,
    :metadata,
    :workspace_id,
    :domain,
    :is_thinking,
    :thinking_status,
    :execution_tracking
  )
  attribute :workspace_id do |message|
    if message.respond_to?(:workspace_id)
      message.workspace_id
    else
      message.workspace&.id
    end
  end

  attribute :audio_url do |message|
    next nil unless message.respond_to?(:audio_file) && message.audio_file.attached?
    prefix = ENV.fetch("API_URL", "http://localhost:8080")
    prefix + Rails.application.routes.url_helpers.rails_blob_url(message.audio_file, only_path: true)
  end

  attribute :has_audio do |message|
    message.respond_to?(:audio_file) && message.audio_file.attached?
  end

  attribute :audio_mime_type do |message|
    next nil unless message.respond_to?(:audio_file) && message.audio_file.attached?
    message.audio_file.content_type
  end
end
