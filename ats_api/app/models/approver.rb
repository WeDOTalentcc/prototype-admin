class Approver < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :user
  belongs_to :department, optional: true

  has_many :approval_requests, dependent: :destroy

  APPROVAL_TYPES = %w[job hiring offer].freeze

  validates :approval_type, presence: true, inclusion: { in: APPROVAL_TYPES }
  validates :approval_level, presence: true, numericality: { greater_than: 0 }
  validates :user_id, uniqueness: {
    scope: [ :account_id, :department_id, :approval_type ],
    conditions: -> { where(is_deleted: false) },
    message: "já é aprovador para este tipo/departamento"
  }

  scope :active, -> { where(is_active: true, is_deleted: false) }
  scope :by_type, ->(type) { where(approval_type: type) }
  scope :by_department, ->(dept_id) { dept_id.present? ? where(department_id: dept_id) : where(department_id: nil) }
  scope :global, -> { where(department_id: nil) }
  scope :ordered, -> { order(:approval_level) }

  def search_data
    {
      id: id,
      account_id: account_id,
      user_id: user_id,
      user_name: user&.name,
      user_email: user&.email,
      department_id: department_id,
      department_name: department&.name,
      approval_type: approval_type,
      approval_level: approval_level,
      limit_value: limit_value,
      name: name.presence || user&.name,
      email: email.presence || user&.email,
      title: title,
      is_active: is_active,
      is_deleted: is_deleted,
      is_global: department_id.nil?,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    [ :name, :email, :user_name, :user_email, :department_name ]
  end

  def self.agg_search_array(_params = {})
    {
      approval_type: { field: "approval_type", limit: 5 },
      approval_level: { field: "approval_level", limit: 10 },
      department_id: { field: "department_id", limit: 20 },
      is_active: { field: "is_active", limit: 2 },
      is_global: { field: "is_global", limit: 2 }
    }
  end

  def self.default_search_order
    { approval_level: :asc }
  end

  def self.for_approval(account_id:, approval_type:, department_id: nil)
    approvers = active.where(account_id: account_id, approval_type: approval_type)
    dept_approvers = approvers.where(department_id: department_id)
    dept_approvers.exists? ? dept_approvers.ordered : approvers.global.ordered
  end

  def display_name
    name.presence || user&.name
  end

  def display_email
    email.presence || user&.email
  end
end
