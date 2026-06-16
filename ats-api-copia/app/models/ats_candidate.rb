# frozen_string_literal: true

class AtsCandidate < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :ats_connection, foreign_key: :connection_id

  validates :connection_id, presence: true
end
