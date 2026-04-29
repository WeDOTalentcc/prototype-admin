# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::NotificationPreferences", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/notification_preferences" do
    context "when authenticated" do
      it "returns preferences (creates default if none exist)" do
        get "/v1/users/notification_preferences", headers: headers

        expect(response).to have_http_status(:ok)

        data = json.dig("data", "attributes")
        expect(data["briefing_enabled"]).to be true
        expect(data["briefing_time"]).to eq("08:00")
        expect(data["alerts"]).to be_a(Hash)
      end

      it "returns existing preferences" do
        create(:notification_preference, user: user, briefing_time: "09:00")

        get "/v1/users/notification_preferences", headers: headers

        expect(response).to have_http_status(:ok)
        expect(json.dig("data", "attributes", "briefing_time")).to eq("09:00")
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/notification_preferences"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe "PUT /v1/users/notification_preferences" do
    context "when authenticated" do
      before { create(:notification_preference, user: user) }

      it "updates preferences" do
        put "/v1/users/notification_preferences", headers: headers, params: {
          briefing_time: "09:30",
          alert_aging_enabled: false,
          aging_threshold_days: 5,
          alert_channels: %w[web whatsapp]
        }

        expect(response).to have_http_status(:ok)

        data = json.dig("data", "attributes")
        expect(data["briefing_time"]).to eq("09:30")
        expect(data["alerts"]["aging"]["enabled"]).to be false
        expect(data["aging_threshold_days"]).to eq(5)
        expect(data["alert_channels"]).to eq(%w[web whatsapp])
      end

      it "rejects invalid briefing_time" do
        put "/v1/users/notification_preferences", headers: headers, params: {
          briefing_time: "invalid"
        }

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end
