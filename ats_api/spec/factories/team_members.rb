FactoryBot.define do
  factory :team_member do
    team
    account { team.account }
    user { association(:user, account: account) }
    role { "member" }
    joined_at { Date.current }
    is_active { true }
  end
end
