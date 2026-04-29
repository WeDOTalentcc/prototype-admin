# frozen_string_literal: true

FactoryBot.define do
  factory :background_agent_step do
    association :background_agent
    association :agent_cycle

    step { "plan" }
    status { "running" }
    message { "Processing step" }
    details { {} }

    trait :done do
      status { "done" }
    end

    trait :error do
      status { "error" }
      message { "Something went wrong" }
    end

    trait :with_narrative do
      narrative { { summary: "Step completed", details: "Full narrative" } }
    end

    BackgroundAgentStep::STEPS.each do |step_name|
      trait step_name.to_sym do
        step { step_name }
      end
    end
  end
end
