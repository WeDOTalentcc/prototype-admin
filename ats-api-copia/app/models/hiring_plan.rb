# frozen_string_literal: true

class HiringPlan < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :department, optional: true

  has_many :planned_headcounts, dependent: :destroy

  validates :company_id, presence: true
end
