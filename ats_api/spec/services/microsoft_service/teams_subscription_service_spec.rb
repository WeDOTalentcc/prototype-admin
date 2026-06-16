# frozen_string_literal: true

require "rails_helper"

RSpec.describe MicrosoftService::TeamsSubscriptionService do
  let(:lia_user) { instance_double(User, id: 1, email: "lia@company.com") }
  let(:chat_id) { "19:abc123@thread.v2" }
  let(:webhook_url) { "https://api.example.com/v1/webhooks/teams_chat" }

  before do
    allow(ENV).to receive(:fetch).with("APP_HOST", "http://localhost:3000").and_return("https://api.example.com")
  end

  describe ".create_or_renew" do
    context "when subscription record does not exist" do
      it "does nothing" do
        allow(TeamsChatSubscription).to receive(:find_by).with(chat_id: chat_id).and_return(nil)

        expect(MicrosoftService::Api).not_to receive(:post)
        described_class.create_or_renew(lia_user, chat_id)
      end
    end

    context "when subscription has no active subscription_id" do
      let(:record) do
        instance_double(
          TeamsChatSubscription,
          chat_id: chat_id,
          subscription_id: nil,
          subscription_expires_at: nil,
          subscription_active?: false
        )
      end

      before do
        allow(TeamsChatSubscription).to receive(:find_by).with(chat_id: chat_id).and_return(record)
        allow(Rails.application.credentials).to receive(:secret_key_base).and_return("a" * 64)
      end

      it "creates a new Graph subscription" do
        api_response = { "id" => "sub-123" }
        allow(MicrosoftService::Api).to receive(:post)
          .with("/subscriptions", lia_user, body: hash_including(changeType: "created"))
          .and_return(api_response)

        allow(record).to receive(:update!)

        described_class.create_or_renew(lia_user, chat_id)

        expect(record).to have_received(:update!).with(
          hash_including(subscription_id: "sub-123", status: "active")
        )
      end

      it "marks as failed when API returns nil" do
        allow(MicrosoftService::Api).to receive(:post).and_return(nil)
        allow(record).to receive(:update!)

        described_class.create_or_renew(lia_user, chat_id)

        expect(record).to have_received(:update!).with(status: "failed")
      end
    end

    context "when subscription is still active" do
      let(:record) do
        instance_double(
          TeamsChatSubscription,
          chat_id: chat_id,
          subscription_id: "sub-existing",
          subscription_expires_at: 30.minutes.from_now,
          subscription_active?: true
        )
      end

      before do
        allow(TeamsChatSubscription).to receive(:find_by).with(chat_id: chat_id).and_return(record)
      end

      it "renews the existing subscription" do
        allow(MicrosoftService::Api).to receive(:patch)
          .with("/subscriptions/sub-existing", lia_user, body: hash_including(:expirationDateTime))
          .and_return({})
        allow(record).to receive(:update!)

        described_class.create_or_renew(lia_user, chat_id)

        expect(MicrosoftService::Api).to have_received(:patch)
        expect(record).to have_received(:update!).with(hash_including(:subscription_expires_at))
      end
    end
  end

  describe ".renew_all_expiring" do
    it "renews all expiring subscriptions" do
      allow(User).to receive(:find_by).with(lia_user: true).and_return(lia_user)

      record = instance_double(TeamsChatSubscription, chat_id: chat_id, subscription_active?: true, subscription_id: "sub-1", subscription_expires_at: 5.minutes.from_now)
      expiring_relation = double("expiring_relation")
      allow(expiring_relation).to receive(:find_each).and_yield(record)
      allow(TeamsChatSubscription).to receive(:expiring_soon).and_return(expiring_relation)
      allow(TeamsChatSubscription).to receive(:find_by).with(chat_id: chat_id).and_return(record)
      allow(MicrosoftService::Api).to receive(:patch).and_return({})
      allow(record).to receive(:update!)

      described_class.renew_all_expiring

      expect(record).to have_received(:update!)
    end

    it "skips when no LIA user exists" do
      allow(User).to receive(:find_by).with(lia_user: true).and_return(nil)

      expect(TeamsChatSubscription).not_to receive(:expiring_soon)
      described_class.renew_all_expiring
    end
  end
end
