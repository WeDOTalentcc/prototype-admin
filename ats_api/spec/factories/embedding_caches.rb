# frozen_string_literal: true

FactoryBot.define do
  factory :embedding_cache do
    association :account

    key { "embedding:#{SecureRandom.hex(32)}" }
    model_version { 'text-embedding-004' }
    query_text { 'ruby developer with 5 years experience' }
    embedding { Array.new(768) { rand(-1.0..1.0) } }
    hit_count { 0 }
    last_accessed_at { Time.current }

    trait :stale do
      last_accessed_at { 31.days.ago }
    end

    trait :popular do
      hit_count { 100 }
      last_accessed_at { 1.hour.ago }
    end
  end
end
