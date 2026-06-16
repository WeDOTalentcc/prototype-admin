FactoryBot.define do
  factory :position_assignment do
    organizational_position
    account { organizational_position.account }
    user { association(:user, account: account) }
    start_date { Date.current }
    is_current { true }
  end
end
