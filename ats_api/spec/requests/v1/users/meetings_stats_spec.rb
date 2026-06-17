# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Meetings#stats", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/meetings/stats" do
    context "when authenticated" do
      before do
        create(:meeting, :completed, organizer: user, account: account)
        create(:meeting, :completed, organizer: user, account: account)
        create(:meeting, :no_show, organizer: user, account: account)
        create(:meeting, :scheduled, organizer: user, account: account)
      end

      it "returns meeting statistics" do
        get "/v1/users/meetings/stats", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["totals"]).to be_a(Hash)
        expect(body["totals"]["total"]).to be_a(Integer)
        expect(body["by_sub_status"]).to be_a(Hash)
        expect(body["by_provider"]).to be_a(Hash)
        expect(body["by_period"]).to be_an(Array)
        expect(body["no_show_rate"]).to be_a(Float)
        expect(body["period"]).to be_a(Hash)
      end

      it "filters by date range" do
        get "/v1/users/meetings/stats", headers: headers, params: {
          start_date: 7.days.ago.to_date.to_s,
          end_date: Date.current.to_s
        }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["period"]["start_date"]).to eq(7.days.ago.to_date.to_s)
      end

      it "filters by organizer_id" do
        get "/v1/users/meetings/stats", headers: headers, params: { organizer_id: user.id }

        expect(response).to have_http_status(:ok)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/meetings/stats"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
