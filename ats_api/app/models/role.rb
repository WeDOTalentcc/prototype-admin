class Role < ApplicationRecord
  include Searchable
  has_many :user_roles, dependent: :destroy
  has_many :users, through: :user_roles
  validates :name, presence: true, uniqueness: { case_sensitive: false }
end
