# frozen_string_literal: true

require "rails_helper"

RSpec.describe Chatbot::WsRateLimiter do
  let(:identifier) { "test-token-#{SecureRandom.hex(4)}" }

  before do
    Sidekiq.redis { |conn| conn.del("ws:rate:triagem:#{identifier}") }
  end

  describe ".record! and .usage" do
    it "records a message and increments usage" do
      expect(described_class.usage(identifier)).to eq(0)
      described_class.record!(identifier)
      expect(described_class.usage(identifier)).to eq(1)
    end
  end

  describe ".exceeded?" do
    it "returns false when under limit" do
      expect(described_class.exceeded?(identifier)).to be false
    end

    it "returns true when at limit" do
      stub_const("Chatbot::WsRateLimiter::LIMIT", 3)
      3.times { described_class.record!(identifier) }
      expect(described_class.exceeded?(identifier)).to be true
    end
  end

  describe ".check!" do
    it "does not raise when under limit" do
      expect { described_class.check!(identifier) }.not_to raise_error
    end

    it "raises WsRateLimitExceeded when at limit" do
      stub_const("Chatbot::WsRateLimiter::LIMIT", 2)
      2.times { described_class.record!(identifier) }

      expect { described_class.check!(identifier) }.to raise_error(Chatbot::WsRateLimitExceeded) do |error|
        expect(error.limit).to eq(2)
        expect(error.retry_after).to eq(60)
      end
    end
  end
end
