# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::AgentTokens", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe "POST /v1/agent_tokens/exchange" do
    context "with valid OTT" do
      let(:ott) { JsonWebToken.encode_ott(account_id: account.id, user_id: user.id) }

      it "returns a service token" do
        post "/v1/agent_tokens/exchange",
             params: { one_time_token: ott }.to_json,
             headers: { "Content-Type" => "application/json" }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["access_token"]).to be_present
        expect(body["token_type"]).to eq("Bearer")
        expect(body["expires_in"]).to be_a(Integer)
        expect(body["user_id"]).to eq(user.id)
      end

      it "rejects the same OTT used twice" do
        post "/v1/agent_tokens/exchange",
             params: { one_time_token: ott }.to_json,
             headers: { "Content-Type" => "application/json" }
        expect(response).to have_http_status(:ok)

        post "/v1/agent_tokens/exchange",
             params: { one_time_token: ott }.to_json,
             headers: { "Content-Type" => "application/json" }
        expect(response).to have_http_status(:conflict)
      end
    end

    context "with missing OTT" do
      it "returns unauthorized" do
        post "/v1/agent_tokens/exchange",
             params: {}.to_json,
             headers: { "Content-Type" => "application/json" }

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context "with invalid OTT" do
      it "returns unauthorized" do
        post "/v1/agent_tokens/exchange",
             params: { one_time_token: "invalid.token.here" }.to_json,
             headers: { "Content-Type" => "application/json" }

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context "with expired OTT" do
      let(:ott) { JsonWebToken.encode_ott(account_id: account.id, user_id: user.id, exp: 1.minute.ago) }

      it "returns unauthorized" do
        post "/v1/agent_tokens/exchange",
             params: { one_time_token: ott }.to_json,
             headers: { "Content-Type" => "application/json" }

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context "with non-OTT token role" do
      let(:regular_token) { JsonWebToken.encode(user_id: user.id) }

      it "returns unauthorized" do
        post "/v1/agent_tokens/exchange",
             params: { one_time_token: regular_token }.to_json,
             headers: { "Content-Type" => "application/json" }

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe "POST /v1/agent_tokens/refresh" do
    context "with valid service token" do
      let(:service_token) do
        JsonWebToken.encode_service_token(account_id: account.id, user_id: user.id)
      end

      it "returns a new service token" do
        post "/v1/agent_tokens/refresh",
             headers: {
               "Authorization" => "Bearer #{service_token}",
               "Content-Type" => "application/json"
             }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["access_token"]).to be_present
        expect(body["access_token"]).not_to eq(service_token)
        expect(body["expires_in"]).to be_a(Integer)
      end
    end

    context "with recently expired service token (within grace period)" do
      let(:expired_token) do
        JsonWebToken.encode_service_token(
          account_id: account.id,
          user_id: user.id,
          exp: 30.seconds.ago
        )
      end

      it "returns a new service token" do
        post "/v1/agent_tokens/refresh",
             headers: {
               "Authorization" => "Bearer #{expired_token}",
               "Content-Type" => "application/json"
             }

        expect(response).to have_http_status(:ok)
        expect(json["access_token"]).to be_present
      end
    end

    context "with token expired beyond grace period" do
      let(:old_token) do
        JsonWebToken.encode_service_token(
          account_id: account.id,
          user_id: user.id,
          exp: 5.minutes.ago
        )
      end

      it "returns unauthorized" do
        post "/v1/agent_tokens/refresh",
             headers: {
               "Authorization" => "Bearer #{old_token}",
               "Content-Type" => "application/json"
             }

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context "with regular user token (non-service role)" do
      let(:user_token) { JsonWebToken.encode(user_id: user.id) }

      it "returns unauthorized" do
        post "/v1/agent_tokens/refresh",
             headers: {
               "Authorization" => "Bearer #{user_token}",
               "Content-Type" => "application/json"
             }

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context "without token" do
      it "returns unauthorized" do
        post "/v1/agent_tokens/refresh",
             headers: { "Content-Type" => "application/json" }

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
