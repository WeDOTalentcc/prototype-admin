# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Candidates#stats", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/candidates/stats" do
    context "when authenticated" do
      before do
        create_list(:candidate, 3, account: account, source: "portal")
        create(:candidate, account: account, source: "linkedin")
      end

      it "returns candidate statistics" do
        get "/v1/users/candidates/stats", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["totals"]).to be_a(Hash)
        expect(body["totals"]["total"]).to eq(4)
        expect(body["by_source"]).to be_a(Hash)
        expect(body["new_per_day"]).to be_an(Array)
        expect(body["by_location"]).to be_a(Hash)
        expect(body["period"]).to be_a(Hash)
      end

      it "filters by source" do
        get "/v1/users/candidates/stats", headers: headers, params: { source: "portal" }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["totals"]["total"]).to eq(3)
      end

      it "accepts date range parameters" do
        get "/v1/users/candidates/stats", headers: headers, params: {
          start_date: 7.days.ago.to_date.to_s,
          end_date: Date.current.to_s
        }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["period"]["start_date"]).to eq(7.days.ago.to_date.to_s)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/candidates/stats"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
