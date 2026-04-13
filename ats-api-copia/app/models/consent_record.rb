# frozen_string_literal: true

class ConsentRecord < ApplicationRecord
  has_many :consent_events, foreign_key: :consent_id, dependent: :destroy

  validates :candidate_id, :consent_type, presence: true
end
