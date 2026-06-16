class Goal < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :user, foreign_key: :user_id, primary_key: :id, optional: true

  validates :name, presence: true
end
