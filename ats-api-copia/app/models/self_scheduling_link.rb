# frozen_string_literal: true

class SelfSchedulingLink < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :interview

  validates :token, presence: true
end
