# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Applies#aging", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/applies/aging" do
    context "when authenticated" do
      let!(:job) { create(:job, user: user, account: account) }
      let!(:sp_screening) { create(:selective_process, job: job, account: account, status: :screening) }

      before do
        create(:apply, job: job, selective_process: sp_screening, account_id: account.id, created_at: 5.days.ago)
        create(:apply, job: job, selective_process: sp_screening, account_id: account.id, created_at: 10.days.ago)
        create(:apply, job: job, selective_process: sp_screening, account_id: account.id, created_at: 1.hour.ago)
      end

      it "returns aging applies in JSON:API format" do
        get "/v1/users/applies/aging", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["data"]).to be_an(Array)
        expect(body["meta"]).to be_a(Hash)
        expect(body["meta"]["total"]).to be_a(Integer)
        expect(body["meta"]["by_severity"]).to be_a(Hash)
        expect(body["meta"]["by_stage"]).to be_a(Hash)
      end

      it "filters by days parameter" do
        get "/v1/users/applies/aging", headers: headers, params: { days: 7 }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["data"]).to be_an(Array)
      end

      it "respects pagination" do
        get "/v1/users/applies/aging", headers: headers, params: { page: 1, per_page: 1 }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["data"].size).to be <= 1
      end

      it "filters by job_id" do
        get "/v1/users/applies/aging", headers: headers, params: { job_id: job.id }

        expect(response).to have_http_status(:ok)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/applies/aging"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
