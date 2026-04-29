# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Emails::CircuitBreaker do
  let(:provider) { :mailgun }
  let(:account_id) { 1 }

  before { Sidekiq.redis { |conn| conn.flushdb } }

  describe ".check!" do
    it "allows request when circuit is closed" do
      expect { described_class.check!(provider: provider, account_id: account_id) }.not_to raise_error
    end

    it "opens circuit after threshold failures" do
      Emails::CircuitBreaker::FAILURE_THRESHOLD.times do
        described_class.record_failure!(provider: provider, account_id: account_id)
      end

      expect { described_class.check!(provider: provider, account_id: account_id) }
        .to raise_error(Emails::CircuitOpen)
    end
  end

  describe ".record_success!" do
    it "closes circuit after success" do
      Emails::CircuitBreaker::FAILURE_THRESHOLD.times do
        described_class.record_failure!(provider: provider, account_id: account_id)
      end

      described_class.record_success!(provider: provider, account_id: account_id)

      expect { described_class.check!(provider: provider, account_id: account_id) }.not_to raise_error
    end
  end
end
