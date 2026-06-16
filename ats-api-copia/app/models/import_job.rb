# frozen_string_literal: true

class ImportJob < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :company_id, presence: true
end
