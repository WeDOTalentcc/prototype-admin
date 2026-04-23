# frozen_string_literal: true

class MeetingRelationship < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :reference, polymorphic: true
  belongs_to :apply, optional: true
  belongs_to :meeting, optional: true
  belongs_to :calendar_event, optional: true

  ROLES = %w[candidate recruiter interviewer client observer].freeze
  validates :role, inclusion: { in: ROLES }, allow_blank: true

  scope :for_account, ->(account_id) { where(account_id: account_id) }
  scope :for_reference, ->(type, id) { where(reference_type: type, reference_id: id) }
  scope :for_meeting, ->(meeting_id) { where(meeting_id: meeting_id) }
  scope :for_calendar_event, ->(calendar_event_id) { where(calendar_event_id: calendar_event_id) }
  scope :with_role, ->(role) { where(role: role) }

  def join_url
    meeting&.join_url || calendar_event&.join_url
  end

  def provider_text
    meeting&.provider_text || calendar_event&.provider_text
  end
end
