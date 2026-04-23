# frozen_string_literal: true

module Llm
  module QuotaPlan
    PLANS = {
      "starter" => {
        monthly_cost_limit_usd: 5.00,
        monthly_request_limit: 5_000,
        burst_rpm: 20
      },
      "pro" => {
        monthly_cost_limit_usd: 25.00,
        monthly_request_limit: 25_000,
        burst_rpm: 50
      },
      "enterprise" => {
        monthly_cost_limit_usd: 100.00,
        monthly_request_limit: 100_000,
        burst_rpm: 100
      }
    }.freeze

    DEFAULT_PLAN = "starter"

    def self.defaults_for(plan_name)
      PLANS.fetch(plan_name, PLANS[DEFAULT_PLAN])
    end
  end
end
