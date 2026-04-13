# frozen_string_literal: true

class WorkforceEntry < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :department, optional: true

  validates :company_id, presence: true
end
