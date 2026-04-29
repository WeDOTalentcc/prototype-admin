# frozen_string_literal: true

FactoryBot.define do
  factory :activity_log do
    reference_type { 'Job' }
    reference_id { 1 }
    action { 'update' }
    changeset { { 'title' => { 'from' => 'Old Title', 'to' => 'New Title' } } }
    ip_address { '127.0.0.1' }

    association :user
    association :account

    trait :create_action do
      action { 'create' }
      changeset { { 'title' => { 'from' => nil, 'to' => 'New Job' } } }
    end

    trait :update_action do
      action { 'update' }
      changeset { { 'title' => { 'from' => 'Old Title', 'to' => 'New Title' } } }
    end

    trait :destroy_action do
      action { 'destroy' }
      changeset { { 'title' => { 'from' => 'Deleted Job', 'to' => nil } } }
    end

    trait :rollback_action do
      action { 'rollback' }
      rolled_back_from_id { 1 }
    end

    trait :with_job_reference do
      association :job
      reference_type { 'Job' }
      reference_id { job.id }
    end

    trait :with_candidate_reference do
      association :candidate
      reference_type { 'Candidate' }
      reference_id { candidate.id }
    end

    trait :complex_changeset do
      changeset do
        {
          'title' => { 'from' => 'Old Title', 'to' => 'New Title' },
          'description' => { 'from' => 'Old Description', 'to' => 'New Description' },
          'status' => { 'from' => 'draft', 'to' => 'published' }
        }
      end
    end

    trait :array_format_changeset do
      changeset do
        {
          'title' => [ 'Old Title', 'New Title' ],
          'description' => [ 'Old Description', 'New Description' ]
        }
      end
    end
  end
end
