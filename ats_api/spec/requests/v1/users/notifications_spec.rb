# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Notifications", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/notifications" do
    context "when authenticated" do
      before do
        create_list(:agent_notification, 3, :sent, user: user)
        create(:agent_notification, :read, user: user)
        create(:agent_notification, :briefing, :sent, user: user)
      end

      it "returns paginated notifications" do
        get "/v1/users/notifications", headers: headers

        expect(response).to have_http_status(:ok)
        expect(json["data"].size).to eq(5)
        expect(json["meta"]["total"]).to eq(5)
        expect(json["meta"]["unread_count"]).to be_a(Integer)
      end

      it "filters by notification_type" do
        get "/v1/users/notifications", headers: headers, params: { notification_type: "briefing" }

        expect(response).to have_http_status(:ok)
        json["data"].each do |notif|
          expect(notif.dig("attributes", "notification_type")).to eq("briefing")
        end
      end

      it "filters by status" do
        get "/v1/users/notifications", headers: headers, params: { status: "read" }

        expect(response).to have_http_status(:ok)
        json["data"].each do |notif|
          expect(notif.dig("attributes", "status")).to eq("read")
        end
      end

      it "paginates results" do
        get "/v1/users/notifications", headers: headers, params: { page: 1, per_page: 2 }

        expect(response).to have_http_status(:ok)
        expect(json["data"].size).to eq(2)
        expect(json["meta"]["total"]).to eq(5)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/notifications"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe "GET /v1/users/notifications/:id" do
    let!(:notification) { create(:agent_notification, :sent, user: user) }

    context "when authenticated" do
      it "returns the notification" do
        get "/v1/users/notifications/#{notification.id}", headers: headers

        expect(response).to have_http_status(:ok)
        expect(json.dig("data", "id")).to eq(notification.id.to_s)
      end

      it "returns not found for another user notification" do
        other_user = create(:user, account: account)
        other_notif = create(:agent_notification, user: other_user)

        get "/v1/users/notifications/#{other_notif.id}", headers: headers

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe "PUT /v1/users/notifications/:id/read" do
    let!(:notification) { create(:agent_notification, :sent, user: user) }

    context "when authenticated" do
      it "marks notification as read" do
        put "/v1/users/notifications/#{notification.id}/read", headers: headers

        expect(response).to have_http_status(:ok)
        expect(notification.reload.read_at).to be_present
        expect(notification.status).to eq("read")
      end
    end
  end

  describe "POST /v1/users/notifications/mark_all_read" do
    before do
      create_list(:agent_notification, 3, :sent, user: user)
    end

    context "when authenticated" do
      it "marks all unread notifications as read" do
        post "/v1/users/notifications/mark_all_read", headers: headers

        expect(response).to have_http_status(:ok)
        expect(user.agent_notifications.unread.count).to eq(0)
      end
    end
  end

  describe "GET /v1/users/notifications/unread_count" do
    before do
      create_list(:agent_notification, 3, :sent, user: user)
      create(:agent_notification, :read, user: user)
    end

    context "when authenticated" do
      it "returns unread count" do
        get "/v1/users/notifications/unread_count", headers: headers

        expect(response).to have_http_status(:ok)
        expect(json["unread_count"]).to eq(3)
      end
    end
  end

  describe "POST /v1/users/notifications/send_push" do
    let(:service_headers) do
      token = JsonWebToken.encode_service_token(account_id: account.id, user_id: user.id, scope: "notifications")
      {
        "Authorization" => "Bearer #{token}",
        "Content-Type" => "application/json"
      }
    end

    context "with service token" do
      it "creates and delivers notification" do
        post "/v1/users/notifications/send_push", headers: service_headers, params: {
          user_id: user.id,
          notification_type: "alert_aging",
          content: "Test alert content",
          channel: "web",
          alert_key: "aging:apply:1:#{Date.current}"
        }.to_json

        expect(response).to have_http_status(:created)
        expect(json["success"]).to be true
      end

      it "rejects duplicate alert_key" do
        create(:agent_notification, user: user, alert_key: "aging:apply:1:#{Date.current}")

        post "/v1/users/notifications/send_push", headers: service_headers, params: {
          user_id: user.id,
          notification_type: "alert_aging",
          content: "Duplicate content",
          channel: "web",
          alert_key: "aging:apply:1:#{Date.current}"
        }.to_json

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json["error"]).to eq("duplicate")
      end
    end

    context "with user token (non-service)" do
      it "returns forbidden" do
        post "/v1/users/notifications/send_push", headers: headers, params: {
          user_id: user.id,
          notification_type: "alert_aging",
          content: "Test",
          channel: "web"
        }.to_json

        expect(response).to have_http_status(:forbidden)
      end
    end
  end
end
