# frozen_string_literal: true

RSpec.describe NotificationPreference, type: :model do
  describe "associations" do
    it { is_expected.to belong_to(:user) }
  end

  describe "validations" do
    subject { build(:notification_preference) }

    it { is_expected.to validate_uniqueness_of(:user_id) }

    it "validates briefing_time format" do
      preference = build(:notification_preference, briefing_time: "25:00")
      expect(preference).not_to be_valid
      expect(preference.errors[:briefing_time]).to be_present
    end

    it "accepts valid briefing_time" do
      preference = build(:notification_preference, briefing_time: "09:30")
      expect(preference).to be_valid
    end

    it "validates briefing_channel inclusion" do
      preference = build(:notification_preference, briefing_channel: "sms")
      expect(preference).not_to be_valid
    end

    it "validates aging_threshold_days range" do
      preference = build(:notification_preference, aging_threshold_days: 0)
      expect(preference).not_to be_valid

      preference.aging_threshold_days = 31
      expect(preference).not_to be_valid
    end

    it "validates alert_channels values" do
      preference = build(:notification_preference, alert_channels: [ "web", "invalid" ])
      expect(preference).not_to be_valid
      expect(preference.errors[:alert_channels]).to be_present
    end
  end

  describe "#alert_settings" do
    let(:preference) { build(:notification_preference, alert_aging_enabled: true, aging_threshold_days: 5) }

    it "returns structured alert settings" do
      settings = preference.alert_settings
      expect(settings[:aging]).to eq({ enabled: true, threshold_days: 5 })
      expect(settings[:deadline]).to eq({ enabled: true })
    end
  end

  describe "#alert_enabled?" do
    let(:preference) { build(:notification_preference, alert_aging_enabled: true, alert_deadline_enabled: false) }

    it "returns true for enabled alert type" do
      expect(preference.alert_enabled?(:aging)).to be true
    end

    it "returns false for disabled alert type" do
      expect(preference.alert_enabled?(:deadline)).to be false
    end

    it "returns false for unknown alert type" do
      expect(preference.alert_enabled?(:unknown)).to be false
    end
  end
end
