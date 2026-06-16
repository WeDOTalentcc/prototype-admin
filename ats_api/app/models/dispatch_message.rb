class DispatchMessage < ApplicationRecord
  belongs_to :account
  belongs_to :dispatch
  belongs_to :recipient, polymorphic: true, optional: true

  enum status: { pending: 0, processing: 1, sent: 2, failed: 3, delivered: 4, opened: 5 }

  has_many :email_tracking_events, dependent: :destroy

  def tracking_pixel_url
    return unless tracking_pixel_token
    "#{Rails.application.credentials.dig(:app, :base_url)}/v1/tracking/pixel/#{tracking_pixel_token}.gif"
  end

  def tracking_click_base_url
    return unless tracking_click_token
    "#{Rails.application.credentials.dig(:app, :base_url)}/v1/tracking/click/#{tracking_click_token}"
  end

  def ensure_unsubscribe_record!
    return unless recipient_id

    EmailUnsubscribe.find_or_create_by(
      account: account,
      candidate_id: recipient_id
    ) do |record|
      record.email = recipient_address || recipient&.try(:email)
    end
  end

  def unsubscribe_url
    return unless recipient_id

    unsubscribe = EmailUnsubscribe.find_by(account: account, candidate_id: recipient_id)
    return unless unsubscribe

    "#{Rails.application.credentials.dig(:app, :base_url)}/v1/email/opt-out/#{unsubscribe.token}"
  end
end
