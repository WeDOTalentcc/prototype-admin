# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::EvaluationCandidates#stats", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/evaluation_candidates/stats" do
    context "when authenticated" do
      it "returns evaluation candidate statistics" do
        get "/v1/users/evaluation_candidates/stats", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["totals"]).to be_a(Hash)
        expect(body["totals"]).to include("total_sent", "completed", "pending", "expired")
        expect(body["completion_rate"]).to be_a(Float).or be_a(Integer)
        expect(body["avg_score"]).to be_a(Float).or be_a(Integer)
        expect(body["score_distribution"]).to be_a(Hash)
        expect(body["by_classification"]).to be_a(Hash)
        expect(body["screening_stats"]).to be_a(Hash)
        expect(body["period"]).to be_a(Hash)
      end

      it "accepts date range params" do
        get "/v1/users/evaluation_candidates/stats", headers: headers, params: {
          start_date: 7.days.ago.to_date.to_s,
          end_date: Date.current.to_s
        }

        expect(response).to have_http_status(:ok)
        expect(json["period"]["start_date"]).to eq(7.days.ago.to_date.to_s)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/evaluation_candidates/stats"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
