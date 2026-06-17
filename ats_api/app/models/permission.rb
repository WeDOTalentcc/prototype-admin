class Permission < ApplicationRecord
  include Searchable

  has_many :role_permissions
  has_many :roles, through: :role_permissions
  has_many :user_permissions
  has_many :users, through: :user_permissions
end
