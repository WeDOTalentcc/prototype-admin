class WhatsappConfigurationSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :environment,
    :phone_number,
    :redirect_url,
    :action_type,
    :description,
    :developer_name,
    :active,
    :priority,
    :is_deleted,
    :deleted_at,
    :metadata,
    :created_at,
    :updated_at
  )

  attribute :formatted_phone do |config|
    config.formatted_phone
  end

  attribute :display_name do |config|
    config.display_name
  end

  attribute :webhook? do |config|
    config.webhook?
  end

  attribute :deleted? do |config|
    config.deleted?
  end
end
