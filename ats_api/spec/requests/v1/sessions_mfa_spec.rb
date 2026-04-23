# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Sessions MFA", type: :request do
  let(:headers) { { "Content-Type" => "application/json" } }
  let(:password) { "password123" }

  describe "POST /v1/sessions with MFA" do
    context "when MFA is not enabled" do
      let(:account) { create(:account, mfa_enabled: false) }
      let(:user) { create(:user, account: account, password: password) }

      it "logs in without MFA challenge" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["token"]).to be_present
        expect(json["user"]["email"]).to eq(user.email)
        expect(json["mfa_required"]).to be_nil
      end
    end

    context "when MFA is enabled for user" do
      let(:account) { create(:account, mfa_enabled: true) }
      let(:user) { create(:user, account: account, password: password, mfa_enabled: true) }

      it "returns MFA challenge" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["mfa_required"]).to eq(true)
        expect(json["mfa_token"]).to be_present
        expect(json["message"]).to include("Código de verificação enviado")
        expect(json["token"]).to be_nil
      end

      it "sends OTP email" do
        expect {
          post "/v1/sessions", params: {
            email: user.email,
            password: password
          }.to_json, headers: headers
        }.to change { ActionMailer::Base.deliveries.count }.by(1)

        email = ActionMailer::Base.deliveries.last
        expect(email.to).to include(user.email)
        expect(email.subject).to include("código de verificação")
      end

      it "masks email in response" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        expect(json["message"]).to match(/\w{2}\*+\w@/)
      end
    end

    context "when MFA is required for admins only" do
      let(:account) { create(:account, mfa_enabled: true, mfa_required_for_admins: true) }
      let(:admin_user) { create(:user, account: account, password: password, is_admin: true) }
      let(:normal_user) { create(:user, account: account, password: password, is_admin: false) }

      it "requires MFA for admin users" do
        post "/v1/sessions", params: {
          email: admin_user.email,
          password: password
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["mfa_required"]).to eq(true)
      end

      it "does not require MFA for normal users" do
        post "/v1/sessions", params: {
          email: normal_user.email,
          password: password
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["token"]).to be_present
        expect(json["mfa_required"]).to be_nil
      end
    end
  end

  describe "POST /v1/sessions/verify_mfa" do
    let(:account) { create(:account, mfa_enabled: true) }
    let(:user) { create(:user, account: account, password: password, mfa_enabled: true) }
    let(:mfa_service) { MfaService.new }

    context "with valid code" do
      it "completes login and returns JWT" do
        # First, trigger MFA challenge
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        mfa_token = json["mfa_token"]

        # Get OTP from Redis
        redis = Redis.new(url: ENV["REDIS_URL"])
        code = redis.get("mfa:otp:#{user.id}")

        # Verify MFA
        post "/v1/sessions/verify_mfa", params: {
          mfa_token: mfa_token,
          code: code
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["token"]).to be_present
        expect(json["user"]["email"]).to eq(user.email)
      end

      it "deletes OTP from Redis after successful verification" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        mfa_token = json["mfa_token"]

        redis = Redis.new(url: ENV["REDIS_URL"])
        code = redis.get("mfa:otp:#{user.id}")

        post "/v1/sessions/verify_mfa", params: {
          mfa_token: mfa_token,
          code: code
        }.to_json, headers: headers

        # Code should be deleted
        expect(redis.get("mfa:otp:#{user.id}")).to be_nil
      end
    end

    context "with invalid code" do
      it "returns error" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        mfa_token = json["mfa_token"]

        post "/v1/sessions/verify_mfa", params: {
          mfa_token: mfa_token,
          code: "000000"
        }.to_json, headers: headers

        expect(response).to have_http_status(:unauthorized)
        json = JSON.parse(response.body)
        expect(json["error"]).to include("inválido ou expirado")
        expect(json["attempts_remaining"]).to be_present
      end
    end

    context "with expired MFA token" do
      it "returns error" do
        expired_token = "invalid.jwt.token"

        post "/v1/sessions/verify_mfa", params: {
          mfa_token: expired_token,
          code: "123456"
        }.to_json, headers: headers

        expect(response).to have_http_status(:unauthorized)
        json = JSON.parse(response.body)
        expect(json["error"]).to include("Token MFA inválido")
      end
    end

    context "rate limiting" do
      it "blocks after max attempts" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        mfa_token = json["mfa_token"]

        # Make 5 failed attempts
        5.times do
          post "/v1/sessions/verify_mfa", params: {
            mfa_token: mfa_token,
            code: "000000"
          }.to_json, headers: headers
        end

        # 6th attempt should be rate limited
        post "/v1/sessions/verify_mfa", params: {
          mfa_token: mfa_token,
          code: "000000"
        }.to_json, headers: headers

        expect(response).to have_http_status(:too_many_requests)
        json = JSON.parse(response.body)
        expect(json["error"]).to include("Limite de tentativas")
        expect(json["rate_limited"]).to eq(true)
      end
    end
  end

  describe "POST /v1/sessions/resend_mfa" do
    let(:account) { create(:account, mfa_enabled: true) }
    let(:user) { create(:user, account: account, password: password, mfa_enabled: true) }

    context "with valid mfa_token" do
      it "resends OTP email" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        mfa_token = json["mfa_token"]

        expect {
          post "/v1/sessions/resend_mfa", params: {
            mfa_token: mfa_token
          }.to_json, headers: headers
        }.to change { ActionMailer::Base.deliveries.count }.by(1)

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["message"]).to include("Novo código enviado")
        expect(json["mfa_token"]).to eq(mfa_token)
      end

      it "generates new OTP code" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        mfa_token = json["mfa_token"]

        redis = Redis.new(url: ENV["REDIS_URL"])
        old_code = redis.get("mfa:otp:#{user.id}")

        post "/v1/sessions/resend_mfa", params: {
          mfa_token: mfa_token
        }.to_json, headers: headers

        new_code = redis.get("mfa:otp:#{user.id}")
        expect(new_code).not_to eq(old_code)
      end
    end

    context "rate limiting resends" do
      it "blocks after 3 resends" do
        post "/v1/sessions", params: {
          email: user.email,
          password: password
        }.to_json, headers: headers

        json = JSON.parse(response.body)
        mfa_token = json["mfa_token"]

        # Make 3 resend requests
        3.times do
          post "/v1/sessions/resend_mfa", params: {
            mfa_token: mfa_token
          }.to_json, headers: headers

          expect(response).to have_http_status(:ok)
        end

        # 4th request should be rate limited
        post "/v1/sessions/resend_mfa", params: {
          mfa_token: mfa_token
        }.to_json, headers: headers

        expect(response).to have_http_status(:too_many_requests)
        json = JSON.parse(response.body)
        expect(json["error"]).to include("Limite de reenvios")
      end
    end

    context "with invalid mfa_token" do
      it "returns error" do
        post "/v1/sessions/resend_mfa", params: {
          mfa_token: "invalid.token"
        }.to_json, headers: headers

        expect(response).to have_http_status(:unauthorized)
        json = JSON.parse(response.body)
        expect(json["error"]).to include("Token MFA inválido")
      end
    end
  end
end
