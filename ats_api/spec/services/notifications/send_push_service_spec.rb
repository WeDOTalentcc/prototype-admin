# frozen_string_literal: true

require "rails_helper"

RSpec.describe Notifications::SendPushService do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  describe "#call" do
    subject(:result) do
      described_class.new(
        user: user,
        notification_type: "alert_aging",
        content: "Test notification",
        channel: "web",
        alert_key: alert_key
      ).call
    end

    let(:alert_key) { "aging:apply:123:#{Date.current}" }

    context "when notification is new" do
      it "creates notification and delivers via ActionCable" do
        expect(ActionCable.server).to receive(:broadcast).with(
          "notifications_user_#{user.id}",
          hash_including(type: "agent_notification")
        )

        expect(result[:success]).to be true
        expect(result[:notification]).to be_a(AgentNotification)
        expect(result[:notification].status).to eq("sent")
      end
    end

    context "when alert_key is duplicate" do
      before { create(:agent_notification, user: user, alert_key: alert_key) }

      it "returns duplicate error" do
        expect(result[:success]).to be false
        expect(result[:error]).to eq("duplicate")
      end
    end

    context "when alert_key is nil" do
      let(:alert_key) { nil }

      it "creates notification without dedup check" do
        expect(ActionCable.server).to receive(:broadcast)

        expect(result[:success]).to be true
      end
    end
  end
end
