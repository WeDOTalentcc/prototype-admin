# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Applies#stats", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/applies/stats" do
    context "when authenticated" do
      let!(:job) { create(:job, user: user, account: account) }
      let!(:sp_screening) { create(:selective_process, job: job, account: account, status: :screening) }
      let!(:sp_rejected) { create(:selective_process, job: job, account: account, status: :rejected) }

      before do
        create_list(:apply, 3, job: job, selective_process: sp_screening, account_id: account.id)
        create_list(:apply, 2, job: job, selective_process: sp_rejected, account_id: account.id)
      end

      it "returns aggregated statistics" do
        get "/v1/users/applies/stats", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["by_status"]).to be_a(Hash)
        expect(body["by_source"]).to be_an(Array)
        expect(body["by_period"]).to be_an(Array)
        expect(body["conversion_rates"]).to be_a(Hash)
        expect(body["totals"]).to be_a(Hash)
        expect(body["totals"]["total"]).to eq(5)
        expect(body["period"]).to be_a(Hash)
      end

      it "filters by job_id" do
        other_job = create(:job, user: user, account: account)
        other_sp = create(:selective_process, job: other_job, account: account)
        create(:apply, job: other_job, selective_process: other_sp, account_id: account.id)

        get "/v1/users/applies/stats", headers: headers, params: { job_id: job.id }

        body = json
        expect(body["totals"]["total"]).to eq(5)
      end

      it "accepts date range parameters" do
        get "/v1/users/applies/stats", headers: headers, params: {
          start_date: 7.days.ago.to_date.to_s,
          end_date: Date.current.to_s
        }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["period"]["start_date"]).to eq(7.days.ago.to_date.to_s)
        expect(body["period"]["end_date"]).to eq(Date.current.to_s)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/applies/stats"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
