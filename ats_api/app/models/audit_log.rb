class AuditLog < ApplicationRecord
  belongs_to :user, optional: true
  belongs_to :account, optional: true
  belongs_to :resource, polymorphic: true, optional: true

  validates :action, presence: true

  scope :recent, -> { order(created_at: :desc) }
  scope :by_user, ->(user) { where(user_id: user.id) }
  scope :by_account, ->(account) { where(account_id: account.id) }
  scope :by_action, ->(action) { where(action: action) }
  scope :by_resource, ->(resource_type, resource_id) { where(resource_type: resource_type, resource_id: resource_id) }
end
