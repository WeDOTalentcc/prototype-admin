# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Emails::RateLimiter do
  let(:provider) { :mailgun }
  let(:account_id) { 1 }

  before { Sidekiq.redis { |conn| conn.flushdb } }

  describe ".check!" do
    it "allows send within limit" do
      expect { described_class.check!(provider: provider, account_id: account_id) }.not_to raise_error
    end

    it "blocks when per_minute limit exceeded" do
      limit = Emails::RateLimiter::LIMITS[:mailgun][:per_minute]
      limit.times { described_class.record_send!(provider: provider, account_id: account_id) }

      expect { described_class.check!(provider: provider, account_id: account_id) }
        .to raise_error(Emails::RateLimitHit)
    end

    it "raises error for unknown provider" do
      expect { described_class.check!(provider: :unknown, account_id: account_id) }
        .to raise_error(ArgumentError, /Unknown provider/)
    end
  end

  describe ".record_send!" do
    it "increments counters in all 3 windows" do
      described_class.record_send!(provider: provider, account_id: account_id)
      usage = described_class.usage(provider: provider, account_id: account_id)

      expect(usage[:min]).to eq(1)
      expect(usage[:hour]).to eq(1)
      expect(usage[:day]).to eq(1)
    end
  end

  describe ".usage" do
    it "returns zero for all windows when no sends" do
      usage = described_class.usage(provider: provider, account_id: account_id)

      expect(usage[:min]).to eq(0)
      expect(usage[:hour]).to eq(0)
      expect(usage[:day]).to eq(0)
    end
  end
end
