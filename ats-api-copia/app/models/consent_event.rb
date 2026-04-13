# frozen_string_literal: true

class ConsentEvent < ApplicationRecord
  belongs_to :consent_record, foreign_key: :consent_id

  validates :consent_id, :event_type, presence: true
end
