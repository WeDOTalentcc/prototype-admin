# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::SourcedProfiles#stats", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/sourced_profiles/stats" do
    context "when authenticated" do
      it "returns sourced profiles statistics" do
        get "/v1/users/sourced_profiles/stats", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["totals"]).to be_a(Hash)
        expect(body["totals"]).to include("total_sourced", "imported_to_candidates", "with_applies", "hired")
        expect(body["conversion_funnel"]).to be_a(Hash)
        expect(body["by_provider"]).to be_an(Array)
        expect(body["by_status"]).to be_a(Hash)
        expect(body["credits"]).to be_a(Hash)
        expect(body["period"]).to be_a(Hash)
      end

      it "accepts date range params" do
        get "/v1/users/sourced_profiles/stats", headers: headers, params: {
          start_date: 7.days.ago.to_date.to_s,
          end_date: Date.current.to_s
        }

        expect(response).to have_http_status(:ok)
        expect(json["period"]["start_date"]).to eq(7.days.ago.to_date.to_s)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/sourced_profiles/stats"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
