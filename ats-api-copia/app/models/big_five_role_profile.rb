class BigFiveRoleProfile < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :name, presence: true
end
