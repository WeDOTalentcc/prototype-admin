# frozen_string_literal: true

require "rails_helper"

RSpec.describe Productivity::ShowService do
  subject(:result) { described_class.new(user: user, start_date: start_date, end_date: end_date).call }

  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:start_date) { 30.days.ago.to_date }
  let(:end_date) { Date.current }

  before { Apartment::Tenant.switch!(account.tenant) }

  it "returns structured productivity data" do
    expect(result).to include(:user_id, :user_name, :period, :jobs, :applies, :interviews, :evaluations)
  end

  it "returns user info" do
    expect(result[:user_id]).to eq(user.id)
    expect(result[:user_name]).to eq(user.name)
  end

  describe ":jobs" do
    before { create_list(:job, 2, user: user, account: account, is_active: true, is_deleted: false, is_archived: false) }

    it "includes active jobs count" do
      expect(result[:jobs][:active]).to eq(2)
    end

    it "includes required keys" do
      expect(result[:jobs]).to include(:active, :created_in_period, :closed_in_period, :avg_days_to_close)
    end
  end

  describe ":applies" do
    it "includes required keys" do
      expect(result[:applies]).to include(:total_received, :hired)
    end
  end

  describe ":interviews" do
    it "includes required keys" do
      expect(result[:interviews]).to include(:conducted, :no_shows, :upcoming_week)
    end
  end

  describe ":evaluations" do
    it "includes required keys" do
      expect(result[:evaluations]).to include(:sent, :completed, :pending)
    end
  end
end
