# frozen_string_literal: true

class AutomatedDecisionExplanation < ApplicationRecord
  validates :candidate_id, presence: true
end
