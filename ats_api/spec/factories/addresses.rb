FactoryBot.define do
  factory :address do
    association :account

    # Associações opcionais — só serão criadas se você passar explicitamente
    city     { nil }
    state    { nil }
    country  { nil }
    user     { nil }

    # Exemplo de campos extras que o Address possa ter:
    street   { "123 Test Street" }
    number   { "10" }
    zip_code  { "12345-678" }
  end
end
