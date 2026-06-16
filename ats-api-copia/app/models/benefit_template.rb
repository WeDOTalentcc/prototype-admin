class BenefitTemplate < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :name, presence: true
end
