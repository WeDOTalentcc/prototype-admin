# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Dispatches", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/dispatches" do
    context "when authenticated" do
      let!(:dispatch1) { create(:dispatch, user: user, account: account, channel_type: "email") }
      let!(:dispatch2) { create(:dispatch, user: user, account: account, channel_type: "whatsapp") }

      it "returns paginated dispatches in JSON:API format" do
        get "/v1/users/dispatches", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["data"]).to be_an(Array)
        expect(body["data"].size).to eq(2)
        expect(body["meta"]["total"]).to eq(2)
      end

      it "filters by channel_type" do
        get "/v1/users/dispatches", headers: headers, params: { channel_type: "email" }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["data"].size).to eq(1)
      end

      it "filters by candidate_id" do
        candidate = create(:candidate, account: account)
        create(:dispatch_message, dispatch: dispatch1, recipient: candidate)

        get "/v1/users/dispatches", headers: headers, params: { candidate_id: candidate.id }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["data"].size).to eq(1)
      end

      it "paginates results" do
        get "/v1/users/dispatches", headers: headers, params: { page: 1, per_page: 1 }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["data"].size).to eq(1)
        expect(body["meta"]["total"]).to eq(2)
        expect(body["meta"]["per_page"]).to eq(1)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/dispatches"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe "GET /v1/users/dispatches/:id" do
    context "when authenticated" do
      let!(:dispatch) { create(:dispatch, user: user, account: account) }

      it "returns dispatch details" do
        get "/v1/users/dispatches/#{dispatch.id}", headers: headers

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["data"]["id"]).to eq(dispatch.id.to_s)
        expect(body["data"]["type"]).to eq("dispatch")
      end

      it "returns not found for invalid id" do
        get "/v1/users/dispatches/0", headers: headers
        expect(response).to have_http_status(:not_found)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/dispatches/1"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
