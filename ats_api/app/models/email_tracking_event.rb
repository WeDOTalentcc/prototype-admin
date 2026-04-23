class EmailTrackingEvent < ApplicationRecord
  belongs_to :dispatch_message
  belongs_to :account, optional: true

  validates :event_type, presence: true
  validates :occurred_at, presence: true

  enum event_type: {
    open: "open",
    click: "click",
    bounce: "bounce",
    unsubscribe: "unsubscribe",
    delivered: "delivered",
    failed: "failed"
  }

  after_create :update_dispatch_message_status

  private

  def update_dispatch_message_status
    case event_type
    when "open"
      dispatch_message&.update(opened_at: occurred_at, status: :opened)
    when "click"
      dispatch_message&.update(clicked_at: occurred_at, clicked_url: url_clicked)
    when "bounce"
      dispatch_message&.update(bounced_at: occurred_at, bounce_reason: metadata["reason"], status: :failed)
    end
  end
end
