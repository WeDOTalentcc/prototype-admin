# frozen_string_literal: true

class SourcedProfileActivity < ApplicationRecord
  belongs_to :sourced_profile
  belongs_to :user

  validates :uid, presence: true, uniqueness: true
  validates :activity_type, presence: true

  before_validation :generate_uid, on: :create

  scope :recent, -> { order(created_at: :desc) }
  scope :by_type, ->(type) { where(activity_type: type) }
  scope :for_profile, ->(profile_id) { where(sourced_profile_id: profile_id) }

  VIEWED = "viewed".freeze
  RATED = "rated".freeze
  STATUS_CHANGED = "status_changed".freeze
  NOTE_ADDED = "note_added".freeze
  IMPORTED = "imported".freeze
  AI_ANALYZED = "ai_analyzed".freeze
  TAG_ADDED = "tag_added".freeze
  TAG_REMOVED = "tag_removed".freeze

  private

  def generate_uid
    self.uid ||= SecureRandom.uuid
  end
end
