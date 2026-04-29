# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Scheduling::Links API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe "GET /v1/users/scheduling/links" do
    let!(:link) { create(:scheduling_link, account: account, created_by: user) }

    it "returns the user's scheduling links" do
      get "/v1/users/scheduling/links", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      expect(json["data"].length).to eq(1)
    end

    it "returns unauthorized without token" do
      get "/v1/users/scheduling/links", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end

    it "filters by status" do
      create(:scheduling_link, :booked, account: account, created_by: user)

      get "/v1/users/scheduling/links", params: { status: "active" }, headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      statuses = json["data"].map { |l| l["attributes"]["status"] }
      expect(statuses).to all(eq("active"))
    end
  end

  describe "GET /v1/users/scheduling/links/:id" do
    let!(:link) { create(:scheduling_link, account: account, created_by: user) }

    it "returns the scheduling link" do
      get "/v1/users/scheduling/links/#{link.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]["attributes"]["token"]).to eq(link.token)
    end

    it "returns 404 for non-existent link" do
      get "/v1/users/scheduling/links/99999", headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end
  end

  describe "POST /v1/users/scheduling/links" do
    let(:valid_params) do
      {
        subject: "Technical Interview",
        duration_minutes: 60,
        interview_type: "online",
        platform: "microsoft_teams",
        message: "Please choose a time slot",
        slots: [
          { start_time: 1.day.from_now.iso8601, end_time: (1.day.from_now + 1.hour).iso8601 },
          { start_time: 2.days.from_now.iso8601, end_time: (2.days.from_now + 1.hour).iso8601 }
        ]
      }
    end

    it "creates a scheduling link with slots" do
      post "/v1/users/scheduling/links", params: valid_params.to_json, headers: auth_headers(user)

      expect(response).to have_http_status(:created)
      expect(json["data"]["attributes"]["subject"]).to eq("Technical Interview")
      expect(json["data"]["attributes"]["slots"].length).to eq(2)
    end

    it "generates a unique token" do
      post "/v1/users/scheduling/links", params: valid_params.to_json, headers: auth_headers(user)

      expect(json["data"]["attributes"]["token"]).to be_present
    end
  end

  describe "PUT /v1/users/scheduling/links/:id" do
    let!(:link) { create(:scheduling_link, account: account, created_by: user) }

    it "updates the link" do
      put "/v1/users/scheduling/links/#{link.id}",
          params: { subject: "Updated Interview" }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(link.reload.subject).to eq("Updated Interview")
    end
  end

  describe "DELETE /v1/users/scheduling/links/:id" do
    let!(:link) { create(:scheduling_link, account: account, created_by: user) }

    it "cancels the link" do
      delete "/v1/users/scheduling/links/#{link.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(link.reload.status).to eq("cancelled")
    end
  end
end
