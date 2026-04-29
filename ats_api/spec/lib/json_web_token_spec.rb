# frozen_string_literal: true

require 'rails_helper'

RSpec.describe JsonWebToken do
  let(:secret) { Rails.application.secret_key_base }

  describe ".encode" do
    it "returns a JWT string" do
      token = described_class.encode({ user_id: 1 })
      expect(token).to be_a(String)
      expect(token.split(".").size).to eq(3)
    end

    it "includes iss, aud, and exp claims" do
      token = described_class.encode({ user_id: 1 })
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["iss"]).to eq(JsonWebToken::ISSUER)
      expect(decoded["aud"]).to eq(JsonWebToken::AUDIENCE)
      expect(decoded["exp"]).to be_present
    end

    it "uses custom expiration" do
      exp = 1.hour.from_now
      token = described_class.encode({ user_id: 1 }, exp)
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["exp"]).to eq(exp.to_i)
    end

    it "preserves payload data" do
      token = described_class.encode({ user_id: 42, account_id: 7 })
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["user_id"]).to eq(42)
      expect(decoded["account_id"]).to eq(7)
    end
  end

  describe ".decode" do
    it "decodes a valid token" do
      token = described_class.encode({ user_id: 1 })
      decoded = described_class.decode(token)

      expect(decoded).to be_a(HashWithIndifferentAccess)
      expect(decoded[:user_id]).to eq(1)
    end

    it "returns nil for expired token" do
      token = described_class.encode({ user_id: 1 }, 1.hour.ago)
      expect(described_class.decode(token)).to be_nil
    end

    it "returns nil for invalid token" do
      expect(described_class.decode("invalid.token.here")).to be_nil
    end

    it "returns nil for token with wrong secret" do
      token = JWT.encode({ user_id: 1, exp: 1.hour.from_now.to_i }, "wrong_secret", "HS256")
      expect(described_class.decode(token)).to be_nil
    end

    it "rejects token without iss/aud claims" do
      payload = { user_id: 1, exp: 1.hour.from_now.to_i }
      token = JWT.encode(payload, secret, "HS256")

      expect(described_class.decode(token)).to be_nil
    end
  end

  describe ".encode_service_token" do
    it "creates a service role token" do
      token = described_class.encode_service_token(account_id: 1, user_id: 2)
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["role"]).to eq("service")
      expect(decoded["account_id"]).to eq(1)
      expect(decoded["user_id"]).to eq(2)
      expect(decoded["jti"]).to be_present
    end

    it "uses custom expiration" do
      exp = 30.minutes.from_now
      token = described_class.encode_service_token(account_id: 1, exp: exp)
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["exp"]).to eq(exp.to_i)
    end

    it "omits nil optional fields" do
      token = described_class.encode_service_token(account_id: 1)
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded).not_to have_key("user_id")
      expect(decoded).not_to have_key("scope")
    end

    it "includes scope when provided" do
      token = described_class.encode_service_token(account_id: 1, scope: "background_agent")
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["scope"]).to eq("background_agent")
    end
  end

  describe ".encode_ott" do
    it "creates a one_time_token role token" do
      token = described_class.encode_ott(account_id: 1, user_id: 2)
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["role"]).to eq("one_time_token")
      expect(decoded["account_id"]).to eq(1)
      expect(decoded["user_id"]).to eq(2)
      expect(decoded["jti"]).to be_present
    end

    it "uses custom expiration" do
      exp = 10.minutes.from_now
      token = described_class.encode_ott(account_id: 1, user_id: 2, exp: exp)
      decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

      expect(decoded["exp"]).to eq(exp.to_i)
    end

    it "defaults to 5 minute expiration" do
      freeze_time do
        token = described_class.encode_ott(account_id: 1, user_id: 2)
        decoded = JWT.decode(token, secret, true, algorithm: "HS256").first

        expect(decoded["exp"]).to eq(5.minutes.from_now.to_i)
      end
    end
  end
end
