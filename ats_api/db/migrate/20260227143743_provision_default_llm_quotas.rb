class ProvisionDefaultLlmQuotas < ActiveRecord::Migration[7.1]
  def up
    if ActiveRecord::Base.connection.table_exists? 'llm_quotas'
      Account.find_each do |account|
        LlmQuota.find_or_create_by!(account_id: account.id) do |quota|
          quota.plan = "starter"
          quota.monthly_cost_limit_usd = 5.0
          quota.monthly_request_limit = 5_000
          quota.burst_rpm = 20
          quota.extra_budget_usd = 0.0
          quota.notify_at_percentage = 80
          quota.enabled = true
          quota.hard_limit = false
          quota.metadata = {}
        end
      end
    end
  end

  def down
    LlmQuota.delete_all if ActiveRecord::Base.connection.table_exists? 'llm_quotas'
  end
end
