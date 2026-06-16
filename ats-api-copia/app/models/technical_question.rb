class TechnicalQuestion < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :title, presence: true
end
