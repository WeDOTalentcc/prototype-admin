class WorkspaceSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :uid,
    :name,
    :is_deleted,
    :last_message_date,
    :domain,
    :domain_reference_id,
    :created_at,
    :updated_at
  )

  belongs_to :user, serializer: UserSerializer
  belongs_to :account, serializer: AccountSerializer

  attribute :has_messages do |workspace|
    workspace.last_message_date.present?
  end

  attribute :last_activity do |workspace|
    workspace.last_message_date || workspace.updated_at
  end

  attribute :messages_count do |workspace|
    workspace.messages_count || 0
  end
end
