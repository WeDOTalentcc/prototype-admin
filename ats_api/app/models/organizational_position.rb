class OrganizationalPosition < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :department
  belongs_to :reports_to, class_name: "OrganizationalPosition", optional: true

  has_many :direct_reports, class_name: "OrganizationalPosition", foreign_key: :reports_to_id, dependent: :nullify
  has_many :position_assignments, dependent: :destroy
  has_many :users, through: :position_assignments
  has_many :jobs, foreign_key: :reports_to_position_id, dependent: :nullify

  validates :title, presence: true

  def self.include_base
    includes(:department, :reports_to)
  end

  def search_data
    {
      title: title,
      description: description,
      level: level,
      position_type: position_type,
      is_active: is_active,
      department_id: department_id,
      department_name: department&.name,
      reports_to_id: reports_to_id,
      reports_to_title: reports_to&.title,
      account_id: account_id
    }
  end

  def self.search_fields
    [ :title, :description, :position_type ]
  end

  def self.agg_search_array(_params = {})
    {
      department_id: { field: "department_id", limit: 20 },
      reports_to_id: { field: "reports_to_id", limit: 20 },
      position_type: { field: "position_type", limit: 10 },
      level: { field: "level", limit: 10 },
      is_active: { field: "is_active", limit: 2 }
    }
  end

  def self.default_search_order
    { level: :asc, title: :asc }
  end

  def current_user
    position_assignments.find_by(is_current: true)&.user
  end

  def reporting_chain
    chain = []
    current = reports_to
    while current
      chain << current
      current = current.reports_to
    end
    chain
  end
end
