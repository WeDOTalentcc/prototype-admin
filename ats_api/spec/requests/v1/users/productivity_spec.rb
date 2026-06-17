# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Productivity#show", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/me/productivity" do
    context "when authenticated" do
      before do
        create_list(:job, 3, user: user, account: account, is_active: true, is_deleted: false, is_archived: false)
      end

      it "returns productivity metrics" do
        get "/v1/users/me/productivity", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["user_id"]).to eq(user.id)
        expect(body["user_name"]).to eq(user.name)
        expect(body["period"]).to be_a(Hash)
        expect(body["jobs"]).to be_a(Hash)
        expect(body["jobs"]["active"]).to be_a(Integer)
        expect(body["applies"]).to be_a(Hash)
        expect(body["interviews"]).to be_a(Hash)
        expect(body["evaluations"]).to be_a(Hash)
      end

      it "accepts date range params" do
        get "/v1/users/me/productivity", headers: headers, params: {
          start_date: 7.days.ago.to_date.to_s,
          end_date: Date.current.to_s
        }

        expect(response).to have_http_status(:ok)
        expect(json["period"]["start_date"]).to eq(7.days.ago.to_date.to_s)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/me/productivity"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
