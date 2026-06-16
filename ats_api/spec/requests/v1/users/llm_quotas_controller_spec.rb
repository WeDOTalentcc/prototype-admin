# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::LlmQuotas API", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account, is_admin: true, roles: [ :admin ]) }
  let!(:regular_user) { create(:user, account: account) }

  describe "GET /v1/users/llm_quotas/current" do
    it "returns quota, usage, and summary for current account" do
      get "/v1/users/llm_quotas/current", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body["success"]).to be true
      expect(body["data"]).to include("quota", "usage", "summary")
    end

    it "auto-provisions a quota when none exists" do
      LlmQuota.where(account_id: account.id).delete_all
      expect { get "/v1/users/llm_quotas/current", headers: auth_headers(user) }
        .to change { LlmQuota.where(account_id: account.id).count }.from(0).to(1)
    end

    it "returns correct quota fields" do
      create(:llm_quota, account: account, plan: "pro", monthly_cost_limit_usd: 25.0)

      get "/v1/users/llm_quotas/current", headers: auth_headers(user)

      body = JSON.parse(response.body)
      quota_data = body["data"]["quota"]
      expect(quota_data["plan"]).to eq("pro")
      expect(quota_data["monthly_cost_limit_usd"]).to eq(25.0)
      expect(quota_data["effective_monthly_limit"]).to eq(25.0)
    end

    it "returns correct usage fields" do
      create(:llm_quota, account: account)
      usage = LlmQuotaUsage.current_for(account.id)
      usage.update!(total_cost_usd: 3.5, total_requests: 150, total_tokens: 50_000)

      get "/v1/users/llm_quotas/current", headers: auth_headers(user)

      body = JSON.parse(response.body)
      usage_data = body["data"]["usage"]
      expect(usage_data["total_cost_usd"]).to eq(3.5)
      expect(usage_data["total_requests"]).to eq(150)
    end

    it "returns correct summary fields" do
      create(:llm_quota, account: account, monthly_cost_limit_usd: 10.0)
      LlmQuotaUsage.current_for(account.id).update!(total_cost_usd: 3.0)

      get "/v1/users/llm_quotas/current", headers: auth_headers(user)

      body = JSON.parse(response.body)
      summary = body["data"]["summary"]
      expect(summary["usage_percentage"]).to eq(30.0)
      expect(summary["cost_remaining_usd"]).to eq(7.0)
      expect(summary["over_limit"]).to be false
      expect(summary["resets_at"]).to be_present
    end
  end

  describe "PATCH /v1/users/llm_quotas/update_current" do
    before { create(:llm_quota, account: account) }

    context "when user is admin" do
      it "updates quota settings" do
        patch "/v1/users/llm_quotas/update_current",
          params: { llm_quota: { notify_at_percentage: 90, hard_limit: true } }.to_json,
          headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["data"]["quota"]["notify_at_percentage"]).to eq(90)
        expect(body["data"]["quota"]["hard_limit"]).to be true
      end
    end

    context "when user is not admin" do
      it "returns forbidden" do
        patch "/v1/users/llm_quotas/update_current",
          params: { llm_quota: { hard_limit: true } }.to_json,
          headers: auth_headers(regular_user)

        expect(response).to have_http_status(:forbidden)
      end
    end
  end
end
