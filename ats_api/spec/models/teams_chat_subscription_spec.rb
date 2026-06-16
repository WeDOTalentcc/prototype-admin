# frozen_string_literal: true

require "rails_helper"

RSpec.describe TeamsChatSubscription, type: :model do
  describe "validations" do
    subject(:subscription) do
      described_class.new(
        lia_user_id: 1,
        recruiter_user_id: 2,
        account_id: 1,
        chat_id: "19:test@thread.v2",
        tenant: "test_tenant",
        status: "active"
      )
    end

    it "is valid with required attributes" do
      allow(User).to receive(:find_by).and_return(instance_double(User))
      allow(Account).to receive(:find_by).and_return(instance_double(Account))

      expect(subscription).to be_valid
    end

    it "requires chat_id" do
      subscription.chat_id = nil
      expect(subscription).not_to be_valid
    end

    it "requires tenant" do
      subscription.tenant = nil
      expect(subscription).not_to be_valid
    end

    it "validates status inclusion" do
      subscription.status = "invalid"
      expect(subscription).not_to be_valid
    end
  end

  describe "#subscription_active?" do
    it "returns true when active with valid subscription" do
      subscription = described_class.new(
        status: "active",
        subscription_id: "sub-123",
        subscription_expires_at: 30.minutes.from_now
      )

      expect(subscription.subscription_active?).to be true
    end

    it "returns false when expired" do
      subscription = described_class.new(
        status: "active",
        subscription_id: "sub-123",
        subscription_expires_at: 5.minutes.ago
      )

      expect(subscription.subscription_active?).to be false
    end

    it "returns false when status is not active" do
      subscription = described_class.new(
        status: "expired",
        subscription_id: "sub-123",
        subscription_expires_at: 30.minutes.from_now
      )

      expect(subscription.subscription_active?).to be false
    end

    it "returns false when no subscription_id" do
      subscription = described_class.new(
        status: "active",
        subscription_id: nil,
        subscription_expires_at: 30.minutes.from_now
      )

      expect(subscription.subscription_active?).to be false
    end
  end

  describe "scopes" do
    describe ".expiring_soon" do
      it "returns active subscriptions expiring within 10 minutes" do
        relation = described_class.expiring_soon
        expect(relation.to_sql).to include("status")
        expect(relation.to_sql).to include("subscription_expires_at")
      end
    end
  end
end
