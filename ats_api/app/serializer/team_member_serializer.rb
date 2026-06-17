class TeamMemberSerializer
  include JSONAPI::Serializer

  attributes :team_id, :user_id, :role, :joined_at, :left_at, :is_active, :account_id, :name, :email, :phone, :position, :linkedin_url

  attribute :user_name do |member|
    member.user&.name
  end
end
