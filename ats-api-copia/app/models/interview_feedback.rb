# frozen_string_literal: true

class InterviewFeedback < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :interview

  validates :interview_id, presence: true
end
