# frozen_string_literal: true

require "rails_helper"

RSpec.describe MfaService do
  let(:user) { create(:user) }
  let(:service) { described_class.new }
  let(:redis) { Redis.new(url: ENV["REDIS_URL"]) }

  after do
    redis.del("mfa:otp:#{user.id}")
    redis.del("mfa:attempts:#{user.id}")
    redis.del("mfa:resend:#{user.id}")
  end

  describe "#generate_otp" do
    it "generates 6-digit numeric code" do
      code = service.generate_otp(user)

      expect(code).to match(/^\d{6}$/)
    end

    it "stores code in Redis with TTL" do
      code = service.generate_otp(user)

      stored_code = redis.get("mfa:otp:#{user.id}")
      expect(stored_code).to eq(code)

      ttl = redis.ttl("mfa:otp:#{user.id}")
      expect(ttl).to be > 0
      expect(ttl).to be <= 300
    end

    it "overwrites previous code" do
      first_code = service.generate_otp(user)
      second_code = service.generate_otp(user)

      expect(first_code).not_to eq(second_code)

      stored_code = redis.get("mfa:otp:#{user.id}")
      expect(stored_code).to eq(second_code)
    end
  end

  describe "#verify_otp" do
    let(:code) { service.generate_otp(user) }

    context "with valid code" do
      it "returns true" do
        expect(service.verify_otp(user, code)).to eq(true)
      end

      it "deletes code from Redis after verification" do
        service.verify_otp(user, code)

        stored_code = redis.get("mfa:otp:#{user.id}")
        expect(stored_code).to be_nil
      end

      it "resets attempts counter" do
        redis.setex("mfa:attempts:#{user.id}", 900, 3)

        service.verify_otp(user, code)

        attempts = redis.get("mfa:attempts:#{user.id}")
        expect(attempts).to be_nil
      end
    end

    context "with invalid code" do
      let!(:code) { service.generate_otp(user) }

      it "returns false" do
        expect(service.verify_otp(user, "000000")).to eq(false)
      end

      it "increments attempts counter" do
        service.verify_otp(user, "000000")

        attempts = redis.get("mfa:attempts:#{user.id}").to_i
        expect(attempts).to eq(1)
      end

      it "does not delete code from Redis" do
        service.verify_otp(user, "000000")

        stored_code = redis.get("mfa:otp:#{user.id}")
        expect(stored_code).to eq(code)
      end
    end

    context "with no code in Redis" do
      it "returns false" do
        expect(service.verify_otp(user, "123456")).to eq(false)
      end
    end

    context "when rate limited" do
      before do
        redis.setex("mfa:attempts:#{user.id}", 900, 5)
      end

      it "returns false without incrementing attempts" do
        attempts_before = redis.get("mfa:attempts:#{user.id}").to_i

        result = service.verify_otp(user, code)

        expect(result).to eq(false)
        attempts_after = redis.get("mfa:attempts:#{user.id}").to_i
        expect(attempts_after).to eq(attempts_before)
      end
    end
  end

  describe "#generate_mfa_token" do
    it "generates valid JWT token" do
      token = service.generate_mfa_token(user)

      expect(token).to be_present
      expect(token.split(".").length).to eq(3)
    end

    it "includes correct payload" do
      token = service.generate_mfa_token(user)
      payload = service.decode_mfa_token(token)

      expect(payload[:role]).to eq("mfa_pending")
      expect(payload[:user_id]).to eq(user.id)
      expect(payload[:iss]).to eq(ENV.fetch("JWT_ISSUER", "ats-api"))
      expect(payload[:aud]).to eq(ENV.fetch("JWT_AUDIENCE", "ats-client"))
      expect(payload[:exp]).to be_present
    end

    it "sets expiration to 10 minutes" do
      token = service.generate_mfa_token(user)
      payload = service.decode_mfa_token(token)

      exp_time = Time.at(payload[:exp])
      expect(exp_time).to be_within(5.seconds).of(10.minutes.from_now)
    end
  end

  describe "#decode_mfa_token" do
    let(:mfa_token) { service.generate_mfa_token(user) }

    it "decodes valid token" do
      payload = service.decode_mfa_token(mfa_token)

      expect(payload).to be_present
      expect(payload[:user_id]).to eq(user.id)
      expect(payload[:role]).to eq("mfa_pending")
    end

    it "returns nil for invalid token" do
      payload = service.decode_mfa_token("invalid.jwt.token")

      expect(payload).to be_nil
    end

    it "returns nil for expired token" do
      expired_payload = {
        role: "mfa_pending",
        user_id: user.id,
        iss: ENV.fetch("JWT_ISSUER", "ats-api"),
        aud: ENV.fetch("JWT_AUDIENCE", "ats-client"),
        exp: 1.hour.ago.to_i
      }
      expired_token = JWT.encode(expired_payload, Rails.application.secret_key_base, "HS256")

      payload = service.decode_mfa_token(expired_token)

      expect(payload).to be_nil
    end

    it "returns nil for nil token" do
      payload = service.decode_mfa_token(nil)

      expect(payload).to be_nil
    end
  end

  describe "#rate_limited?" do
    it "returns false when under limit" do
      expect(service.rate_limited?(user)).to eq(false)
    end

    it "returns false with 4 attempts" do
      redis.setex("mfa:attempts:#{user.id}", 900, 4)

      expect(service.rate_limited?(user)).to eq(false)
    end

    it "returns true with 5 attempts" do
      redis.setex("mfa:attempts:#{user.id}", 900, 5)

      expect(service.rate_limited?(user)).to eq(true)
    end

    it "returns true with more than 5 attempts" do
      redis.setex("mfa:attempts:#{user.id}", 900, 10)

      expect(service.rate_limited?(user)).to eq(true)
    end
  end

  describe "#attempts_remaining" do
    it "returns 5 when no attempts made" do
      expect(service.attempts_remaining(user)).to eq(5)
    end

    it "returns 4 after 1 attempt" do
      redis.setex("mfa:attempts:#{user.id}", 900, 1)

      expect(service.attempts_remaining(user)).to eq(4)
    end

    it "returns 0 after 5 attempts" do
      redis.setex("mfa:attempts:#{user.id}", 900, 5)

      expect(service.attempts_remaining(user)).to eq(0)
    end

    it "returns 0 when exceeded limit" do
      redis.setex("mfa:attempts:#{user.id}", 900, 10)

      expect(service.attempts_remaining(user)).to eq(0)
    end
  end
end
