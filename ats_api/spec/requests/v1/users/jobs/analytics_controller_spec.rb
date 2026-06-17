# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Jobs::Analytics API", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  let(:job) { create(:job, user: user, account: account, published_date: 10.days.ago) }

  let(:sp_funnel) { create(:selective_process, job: job, account: account, name: "Funnel", position: 0, status: :web_submission) }
  let(:sp_screening) { create(:selective_process, job: job, account: account, name: "Screening", position: 1, status: :screening) }

  describe "GET /v1/users/jobs/:id/analytics" do
    context "when authenticated" do
      before do
        sp_funnel
        sp_screening
      end

      it "returns analytics data" do
        get "/v1/users/jobs/#{job.id}/analytics", headers: authentication_headers

        expect(response).to have_http_status(:ok)

        body = JSON.parse(response.body)
        expect(body["success"]).to be true
        expect(body["data"]).to be_a(Hash)
        expect(body["data"]["overview"]).to be_present
        expect(body["data"]["funnel"]).to be_present
        expect(body["data"]["velocity"]).to be_present
        expect(body["data"]["quality"]).to be_present
        expect(body["data"]["sources"]).to be_present
        expect(body["data"]["engagement"]).to be_present
        expect(body["data"]["scheduling"]).to be_present
        expect(body["data"]["team_activity"]).to be_present
        expect(body["data"]["computed_at"]).to be_present
      end

      it "returns funnel stages matching selective processes" do
        get "/v1/users/jobs/#{job.id}/analytics", headers: authentication_headers

        body = JSON.parse(response.body)
        stages = body["data"]["funnel"]["stages"]
        stage_names = stages.map { |s| s["name"] }

        expect(stage_names).to include("Funnel", "Screening")
      end
    end

    context "when using force_refresh" do
      before { sp_funnel }

      it "forces recomputation" do
        get "/v1/users/jobs/#{job.id}/analytics", params: { force_refresh: true }, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["data"]["computed_at"]).to be_present
      end
    end

    context "when job does not exist" do
      it "returns not found" do
        get "/v1/users/jobs/0/analytics", headers: authentication_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context "when job belongs to another account" do
      let(:other_account) { create(:account) }
      let(:other_user) { create(:user, account: other_account) }
      let(:other_job) { create(:job, user: other_user, account: other_account) }

      it "returns forbidden" do
        get "/v1/users/jobs/#{other_job.id}/analytics", headers: authentication_headers

        expect(response).to have_http_status(:forbidden)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/jobs/#{job.id}/analytics"

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context "when analytics snapshot is cached" do
      let(:cached_data) do
        {
          overview: { total_applies: 42 },
          funnel: { stages: [] },
          computed_at: Time.current.iso8601
        }
      end

      before do
        sp_funnel
        allow(Rails.cache).to receive(:read)
          .with(Jobs::AnalyticsService.cache_key(job.id))
          .and_return(cached_data)
      end

      it "returns cached data without recomputing" do
        get "/v1/users/jobs/#{job.id}/analytics", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body["data"]["overview"]["total_applies"]).to eq(42)
      end
    end
  end
end
