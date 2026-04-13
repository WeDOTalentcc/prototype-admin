class BigFiveQuestion < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :text, presence: true
  validates :trait, presence: true
end
