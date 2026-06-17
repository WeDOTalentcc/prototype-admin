# frozen_string_literal: true

class PlannedHeadcount < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :hiring_plan

  validates :hiring_plan_id, presence: true
end
