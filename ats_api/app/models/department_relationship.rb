class DepartmentRelationship < ApplicationRecord
  include Searchable

  belongs_to :department
  belongs_to :user, optional: true
  belongs_to :account
  belongs_to :reference, polymorphic: true

  ROLES = %w[manager member lead].freeze

  validates :reference_type, :reference_id, presence: true
  validates :role, inclusion: { in: ROLES }
  validates :user_id, uniqueness: { scope: %i[department_id is_deleted], conditions: -> { where(is_deleted: false) } }, allow_nil: true

  scope :active, -> { where(is_deleted: false) }
  scope :managers, -> { where(role: "manager", is_deleted: false) }
  scope :members, -> { where(role: "member", is_deleted: false) }

  def search_data
    {
      id: id,
      department_id: department_id,
      department_name: department&.name,
      user_id: user_id,
      user_name: user&.name,
      reference_type: reference_type,
      reference_id: reference_id,
      role: role,
      title: title,
      is_primary: is_primary,
      is_deleted: is_deleted,
      account_id: account_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    %i[role title]
  end
end
