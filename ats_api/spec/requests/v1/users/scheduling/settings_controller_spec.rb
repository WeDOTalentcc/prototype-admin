# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Scheduling::Settings API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe "GET /v1/users/scheduling/settings" do
    context "when settings exist" do
      let!(:settings) { create(:scheduling_setting, user: user, account: account) }

      it "returns the user settings" do
        get "/v1/users/scheduling/settings", headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(json["timezone"]).to eq(settings.timezone)
      end
    end

    context "when settings do not exist" do
      it "auto-creates default settings" do
        get "/v1/users/scheduling/settings", headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(SchedulingSetting.exists?(user: user)).to be true
      end
    end

    it "returns unauthorized without token" do
      get "/v1/users/scheduling/settings", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /v1/users/scheduling/settings" do
    let!(:settings) { create(:scheduling_setting, user: user, account: account) }

    it "updates scheduling settings" do
      put "/v1/users/scheduling/settings",
          params: { timezone: "America/New_York", default_duration_minutes: 30 }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(settings.reload.timezone).to eq("America/New_York")
      expect(settings.reload.default_duration_minutes).to eq(30)
    end

    it "returns unauthorized without token" do
      put "/v1/users/scheduling/settings",
          params: { timezone: "UTC" }.to_json,
          headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end
end
