# frozen_string_literal: true

FactoryBot.define do
  factory :entity_column do
    entity { 'candidate' }
    requested { 'default' }
    is_main { false }
    is_views { false }
    is_public { false }
    columns_view { [] }
    business_ids { [] }

    account_id { create(:account).id }
    association :user, factory: :user

    trait :public do
      is_public { true }
    end

    trait :main do
      is_main { true }
    end

    trait :view do
      is_views { true }
      label { 'Custom View' }
    end

    trait :shortlist do
      requested { 'shortlists' }
    end

    trait :job_specific do
      association :job
    end

    trait :shortlist_specific do
      association :shortlist
    end

    trait :with_columns do
      columns_view do
        [
          {
            value: 'name',
            text: 'Name',
            sortable: true,
            type: 'text',
            filter: 'text',
            width: 'auto'
          },
          {
            value: 'email',
            text: 'Email',
            sortable: true,
            type: 'text',
            filter: 'text',
            width: 'auto'
          }
        ]
      end
    end

    trait :apply_entity do
      entity { 'apply' }
      requested { 'job' }
    end

    trait :education_entity do
      entity { 'education' }
    end

    trait :with_business_ids do
      business_ids { [ 1, 2, 3 ] }
    end
  end
end
