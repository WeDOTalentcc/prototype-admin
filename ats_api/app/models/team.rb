class Team < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :account
  belongs_to :department, optional: true
  belongs_to :team_lead, class_name: "User", optional: true

  has_many :team_members, dependent: :destroy
  has_many :users, through: :team_members
  has_many :jobs, dependent: :nullify

  validates :name, presence: true, uniqueness: { scope: :account_id }

  def self.include_base
    includes(:department, :team_lead)
  end

  def search_data
    {
      name: name,
      description: description,
      department_id: department_id,
      department_name: department&.name,
      team_lead_id: team_lead_id,
      team_lead_name: team_lead&.name,
      member_count: member_count,
      is_active: is_active,
      account_id: account_id
    }
  end

  def self.search_fields
    [ :name, :description ]
  end

  def self.agg_search_array(_params = {})
    {
      department_id: { field: "department_id", limit: 20 },
      team_lead_id: { field: "team_lead_id", limit: 20 },
      is_active: { field: "is_active", limit: 2 }
    }
  end

  def self.default_search_order
    { name: :asc }
  end

  def current_composition
    team_members.includes(:user).where(is_active: true).map do |member|
      {
        user_id: member.user_id,
        name: member.user&.name,
        role: member.role
      }
    end
  end
end
