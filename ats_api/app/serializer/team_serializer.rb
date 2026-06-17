class TeamSerializer
  include JSONAPI::Serializer

  attributes :name, :description, :department_id, :team_lead_id, :member_count, :is_active, :account_id

  attribute :department_name do |team|
    team.department&.name
  end

  attribute :team_lead_name do |team|
    team.team_lead&.name
  end

  attribute :current_composition do |team|
    team.current_composition
  end
end
