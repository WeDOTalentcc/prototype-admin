class Message < ApplicationRecord
  include Searchable

  belongs_to :account, optional: true

  validates :reference_type, presence: true
  validates :reference_id, presence: true

  STATUS_NOT_ANSWERED = 0
  STATUS_ANSWERED = 1

  ROLE_SYSTEM = 0
  ROLE_USER = 1

  after_create_commit :publish_message_event

  private

  def publish_message_event
    return unless reference_type == "User"

    MessageService::EventPublisher.publish(
      message_id: id,
      reference_type: reference_type,
      reference_id: reference_id,
      content: content,
      status: status,
      entity: entity,
      created_at: created_at.iso8601
    )
  end
end
