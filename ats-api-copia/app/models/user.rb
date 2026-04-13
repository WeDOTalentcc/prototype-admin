class User < ApplicationRecord
  # searchkick
  include Searchable
  
  belongs_to :account, optional: true
  has_many :jobs, dependent: :destroy
  has_secure_password

  validates :email, presence: true, uniqueness: { case_sensitive: false }

  has_many :user_roles
  has_many :roles, through: :user_roles
  has_many :role_permissions, through: :roles

  has_many :user_permissions
  has_many :direct_permissions, through: :user_permissions, source: :permission

  def can?(permission_name)
    permissions.exists?(name: permission_name) || direct_permissions.exists?(name: permission_name)
  end

  def effective_permissions
    (permissions + direct_permissions).uniq
  end

end
