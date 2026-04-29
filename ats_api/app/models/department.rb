class Department < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :account
  belongs_to :parent_department, class_name: "Department", optional: true
  belongs_to :manager, class_name: "User", optional: true

  has_many :child_departments, -> { where(is_deleted: false) }, class_name: "Department", foreign_key: :parent_department_id, dependent: :nullify
  has_many :organizational_positions, dependent: :destroy
  has_many :teams, dependent: :nullify
  has_many :jobs, dependent: :nullify
  has_many :department_relationships, -> { where(is_deleted: false) }, dependent: :destroy
  has_many :members, through: :department_relationships, source: :user
  has_many :approvers, dependent: :nullify

  scope :active, -> { where(is_deleted: false) }

  validates :name, presence: true, uniqueness: { scope: :account_id }

  def self.include_base
    includes(:manager, :parent_department, :child_departments)
  end

  def search_data
    {
      name: name,
      description: description,
      level: level,
      parent_department_id: parent_department_id,
      parent_department_name: parent_department&.name,
      manager_id: manager_id,
      manager_name: manager&.name,
      manager_email: manager_email,
      manager_title: manager_title,
      color: color,
      headcount: headcount,
      order: order,
      account_id: account_id,
      is_deleted: is_deleted,
      children_count: child_departments.size,
      created_at: created_at
    }
  end

  def self.search_fields
    [ :name, :description ]
  end

  def self.agg_search_array(_params = {})
    {
      level: { field: "level", limit: 10 },
      manager_id: { field: "manager_id", limit: 20 },
      parent_department_id: { field: "parent_department_id", limit: 20 }
    }
  end

  def self.default_search_order
    { level: :asc, name: :asc }
  end

  def descendants
    child_departments.flat_map { |child| [ child ] + child.descendants }
  end

  def ancestors
    list = []
    current = parent_department
    while current
      list.unshift(current)
      current = current.parent_department
    end
    list
  end
end
