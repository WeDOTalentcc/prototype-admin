FactoryBot.define do
  factory :occupation do
    name { "Developer" }
    is_deleted { false }
    account
    user
  end
end
