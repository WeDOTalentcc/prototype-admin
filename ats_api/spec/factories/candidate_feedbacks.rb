# frozen_string_literal: true

FactoryBot.define do
  factory :candidate_feedback do
    association :account
    association :user
    sourcing { nil }
    apply { nil }
    candidate { nil }
    job { nil }
    sourced_profile_sourcing { nil }

    feedback_type { 'like' }
    is_deleted { false }
    search_query_snapshot { {} }
    candidate_score_snapshot { {} }

    trait :with_sourcing do
      association :sourcing
      association :candidate
    end

    trait :with_apply do
      association :apply
    end

    trait :with_sourced_profile_sourcing do
      association :sourced_profile_sourcing
    end

    trait :dislike do
      feedback_type { 'dislike' }
    end

    trait :deleted do
      is_deleted { true }
    end

    trait :with_snapshots do
      search_query_snapshot do
        {
          'query' => 'desenvolvedor ruby',
          'provider' => 'pearch',
          'searched_at' => Time.current.iso8601
        }
      end

      candidate_score_snapshot do
        {
          'sourcing_score' => 85.5,
          'search_source' => 'hybrid',
          'search_score' => 90.0
        }
      end
    end
  end
end
