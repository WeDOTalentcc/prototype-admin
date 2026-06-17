# frozen_string_literal: true

RSpec.describe AgentNotification, type: :model do
  describe "associations" do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to belong_to(:reference).optional }
  end

  describe "validations" do
    subject { build(:agent_notification) }

    it { is_expected.to validate_presence_of(:notification_type) }
    it { is_expected.to validate_presence_of(:channel) }
    it { is_expected.to validate_presence_of(:status) }
    it { is_expected.to validate_inclusion_of(:notification_type).in_array(AgentNotification::NOTIFICATION_TYPES) }
    it { is_expected.to validate_inclusion_of(:channel).in_array(AgentNotification::CHANNELS) }
    it { is_expected.to validate_inclusion_of(:status).in_array(AgentNotification::STATUSES) }
    it { is_expected.to validate_uniqueness_of(:alert_key).allow_nil }
  end

  describe "scopes" do
    let!(:user) { create(:user) }
    let!(:unread) { create(:agent_notification, :sent, user: user) }
    let!(:read_notification) { create(:agent_notification, :read, user: user) }
    let!(:failed) { create(:agent_notification, :failed, user: user) }

    describe ".unread" do
      it "returns notifications without read_at excluding failed" do
        expect(described_class.unread).to contain_exactly(unread)
      end
    end

    describe ".by_type" do
      it "filters by notification_type" do
        expect(described_class.by_type("alert_aging")).to include(unread)
      end
    end

    describe ".by_status" do
      it "filters by status" do
        expect(described_class.by_status("read")).to contain_exactly(read_notification)
      end
    end
  end

  describe "#mark_as_read!" do
    let(:notification) { create(:agent_notification, :sent) }

    it "sets read_at and status" do
      notification.mark_as_read!
      expect(notification.reload.read_at).to be_present
      expect(notification.status).to eq("read")
    end

    it "does not update if already read" do
      notification.update!(read_at: 1.hour.ago, status: "read")
      original_read_at = notification.read_at

      notification.mark_as_read!
      expect(notification.reload.read_at).to eq(original_read_at)
    end
  end

  describe "#mark_as_sent!" do
    let(:notification) { create(:agent_notification) }

    it "sets sent_at and status" do
      notification.mark_as_sent!
      expect(notification.reload.sent_at).to be_present
      expect(notification.status).to eq("sent")
    end
  end
end
