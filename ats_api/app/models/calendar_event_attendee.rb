# frozen_string_literal: true

class CalendarEventAttendee < ApplicationRecord
  RESPONSE_STATUSES = {
    not_responded: "not_responded",
    accepted: "accepted",
    declined: "declined",
    tentative: "tentative",
    organizer: "organizer"
  }.freeze

  MICROSOFT_RESPONSE_MAP = {
    "notResponded" => RESPONSE_STATUSES[:not_responded],
    "none" => RESPONSE_STATUSES[:not_responded],
    "accepted" => RESPONSE_STATUSES[:accepted],
    "declined" => RESPONSE_STATUSES[:declined],
    "tentativelyAccepted" => RESPONSE_STATUSES[:tentative],
    "organizer" => RESPONSE_STATUSES[:organizer]
  }.freeze

  belongs_to :calendar_event
  belongs_to :user, optional: true

  validates :email, presence: true, format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :response_status, inclusion: { in: RESPONSE_STATUSES.values }
  validates :email, uniqueness: { scope: :calendar_event_id }

  before_validation :normalize_email
  before_validation :link_user_by_email, if: -> { user_id.nil? && email.present? }
  before_save :set_organizer_status, if: :is_organizer?

  scope :organizers, -> { where(is_organizer: true) }
  scope :guests, -> { where(is_organizer: false) }
  scope :accepted, -> { where(response_status: RESPONSE_STATUSES[:accepted]) }
  scope :declined, -> { where(response_status: RESPONSE_STATUSES[:declined]) }

  def self.from_microsoft_payload(payload, is_organizer: false)
    {
      name: payload.dig("emailAddress", "name"),
      email: payload.dig("emailAddress", "address")&.downcase,
      response_status: MICROSOFT_RESPONSE_MAP.fetch(
        payload.dig("status", "response") || (is_organizer ? "organizer" : "notResponded"),
        RESPONSE_STATUSES[:not_responded]
      ),
      responded_at: payload.dig("status", "time")&.to_time,
      is_organizer: is_organizer
    }
  end

  def accepted?
    response_status == RESPONSE_STATUSES[:accepted]
  end

  def declined?
    response_status == RESPONSE_STATUSES[:declined]
  end

  private

  def normalize_email
    self.email = email&.downcase&.strip
  end

  def link_user_by_email
    self.user = User.find_by(email: email)
  end

  def set_organizer_status
    self.response_status = RESPONSE_STATUSES[:organizer]
  end
end
