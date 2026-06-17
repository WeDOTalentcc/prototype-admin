require 'rails_helper'

RSpec.describe "V1::Sessions API", type: :request do
  let(:user) { create(:user, password: "password123") }
  let(:headers) { { "Content-Type" => "application/json" } }

  describe "POST /v1/sessions" do
    context "with valid credentials" do
      it "returns token and user" do
        post "/v1/sessions", params: {
          email: user.email,
          password: "password123"
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["token"]).to be_present
        expect(json["user"]["email"]).to eq(user.email)
      end
    end

    context "with invalid credentials" do
      it "returns unauthorized" do
        post "/v1/sessions", params: {
          email: user.email,
          password: "wrong"
        }.to_json, headers: headers

        expect(response).to have_http_status(:unauthorized)
        json = JSON.parse(response.body)
        expect(json["error"]).to eq("Invalid email or password")
      end
    end
  end

  describe "GET /v1/me" do
    context "with valid token" do
      let(:token) { JWT.encode({ user_id: user.id }, Rails.application.secret_key_base) }

      it "returns current user" do
        get "/v1/me", headers: headers.merge("Authorization" => "Bearer #{token}")

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["user"]["email"]).to eq(user.email)
      end
    end

    context "without token" do
      it "returns unauthorized" do
        get "/v1/me", headers: headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe "POST /v1/logout" do
    let(:token) { JWT.encode({ user_id: user.id }, Rails.application.secret_key_base) }

    it "returns logout message" do
      post "/v1/logout", headers: headers.merge("Authorization" => "Bearer #{token}")

      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json["message"]).to eq("Logged out")
    end
  end
end
