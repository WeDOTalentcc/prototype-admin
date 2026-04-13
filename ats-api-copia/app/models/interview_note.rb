# frozen_string_literal: true

class InterviewNote < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :interview

  validates :interview_id, presence: true
end
