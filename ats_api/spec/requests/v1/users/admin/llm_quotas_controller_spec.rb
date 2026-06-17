# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Admin::LlmQuotas API", type: :request do
  let!(:super_admin) { create(:user, roles: [ :super_admin ]) }
  let!(:regular_user) { create(:user, roles: [ :user ]) }
  let!(:target_account) { create(:account) }
  let!(:quota) { create(:llm_quota, account: target_account) }

  def auth_headers_for(user)
    { "Authorization" => "Bearer #{JsonWebToken.encode(user_id: user.id)}", "Content-Type" => "application/json" }
  end

  describe "GET /v1/users/admin/llm_quotas" do
    context "when user is super_admin" do
      it "returns list of all quotas" do
        get "/v1/users/admin/llm_quotas", headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["success"]).to be true
        expect(body["data"]).to be_an(Array)
        expect(body["data"].first).to include("account_id", "plan", "current_usage")
      end

      it "filters by plan" do
        create(:llm_quota, :pro, account: create(:account))
        get "/v1/users/admin/llm_quotas", params: { plan: "pro" }, headers: auth_headers_for(super_admin)

        body = JSON.parse(response.body)
        plans = body["data"].map { |q| q["plan"] }.uniq
        expect(plans).to eq([ "pro" ])
      end

      it "filters by enabled" do
        create(:llm_quota, :disabled, account: create(:account))
        get "/v1/users/admin/llm_quotas", params: { enabled: false }, headers: auth_headers_for(super_admin)

        body = JSON.parse(response.body)
        enabled_values = body["data"].map { |q| q["enabled"] }.uniq
        expect(enabled_values).to eq([ false ])
      end
    end

    context "when user is a regular user" do
      it "returns forbidden" do
        get "/v1/users/admin/llm_quotas", headers: auth_headers_for(regular_user)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe "GET /v1/users/admin/llm_quotas/:id" do
    context "when user is super_admin" do
      it "returns the quota with usage" do
        get "/v1/users/admin/llm_quotas/#{quota.id}", headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["data"]["id"]).to eq(quota.id)
        expect(body["data"]["current_usage"]).to include("period", "total_cost_usd", "total_requests")
      end
    end

    context "when quota does not exist" do
      it "returns not found" do
        get "/v1/users/admin/llm_quotas/99999", headers: auth_headers_for(super_admin)
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe "PUT /v1/users/admin/llm_quotas/:id" do
    context "when user is super_admin" do
      it "updates the quota plan and limits" do
        put "/v1/users/admin/llm_quotas/#{quota.id}",
          params: { llm_quota: { plan: "pro", monthly_cost_limit_usd: 25.0, monthly_request_limit: 25_000, burst_rpm: 50 } }.to_json,
          headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["data"]["plan"]).to eq("pro")
        expect(body["data"]["monthly_cost_limit_usd"]).to eq(25.0)
      end

      it "toggles enabled flag" do
        put "/v1/users/admin/llm_quotas/#{quota.id}",
          params: { llm_quota: { enabled: false } }.to_json,
          headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        expect(quota.reload.enabled).to be false
      end

      it "toggles hard_limit flag" do
        put "/v1/users/admin/llm_quotas/#{quota.id}",
          params: { llm_quota: { hard_limit: true } }.to_json,
          headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        expect(quota.reload.hard_limit).to be true
      end
    end
  end

  describe "POST /v1/users/admin/llm_quotas/:id/grant_extra" do
    context "when user is super_admin" do
      it "grants extra budget" do
        post "/v1/users/admin/llm_quotas/#{quota.id}/grant_extra",
          params: { extra_budget_usd: 10.0, reason: "Sprint capacity" }.to_json,
          headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["message"]).to include("$10.0")
        expect(quota.reload.extra_budget_usd).to eq(10.0)
      end

      it "grants extra budget with expiration" do
        expires = 1.month.from_now.iso8601
        post "/v1/users/admin/llm_quotas/#{quota.id}/grant_extra",
          params: { extra_budget_usd: 5.0, expires_at: expires, reason: "Temporary" }.to_json,
          headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        expect(quota.reload.extra_budget_expires_at).to be_present
      end
    end
  end

  describe "POST /v1/users/admin/llm_quotas/:id/reset_usage" do
    context "when user is super_admin" do
      it "resets usage counters to zero" do
        usage = LlmQuotaUsage.current_for(target_account.id)
        usage.update!(total_cost_usd: 10.0, total_requests: 500, total_tokens: 100_000)

        post "/v1/users/admin/llm_quotas/#{quota.id}/reset_usage",
          headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["message"]).to include("Usage reset")

        usage.reload
        expect(usage.total_cost_usd.to_f).to eq(0.0)
        expect(usage.total_requests).to eq(0)
        expect(usage.total_tokens).to eq(0)
      end
    end
  end
end
