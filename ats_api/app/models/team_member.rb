class TeamMember < ApplicationRecord
  include Searchable

  belongs_to :team
  belongs_to :user
  belongs_to :account

  scope :active, -> { where(is_active: true) }

  validates :team_id, uniqueness: { scope: [ :user_id, :is_active ] }

  def self.include_base
    includes(:team, :user)
  end

  def search_data
    {
      team_id: team_id,
      team_name: team&.name,
      user_id: user_id,
      user_name: user&.name,
      role: role,
      joined_at: joined_at,
      left_at: left_at,
      is_active: is_active,
      account_id: account_id,
      name: name,
      email: email,
      phone: phone,
      position: position,
      linkedin_url: linkedin_url
    }
  end

  def self.search_fields
    [ :role, :team_name, :user_name ]
  end

  def self.agg_search_array(_params = {})
    {
      team_id: { field: "team_id", limit: 20 },
      user_id: { field: "user_id", limit: 20 },
      role: { field: "role", limit: 10 },
      is_active: { field: "is_active", limit: 2 }
    }
  end

  def self.default_search_order
    { joined_at: :desc }
  end
end
