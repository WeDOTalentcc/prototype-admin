# frozen_string_literal: true

require "rails_helper"

RSpec.describe SourcedProfiles::StatsService do
  subject(:result) { described_class.new(start_date: start_date, end_date: end_date).call }

  let(:start_date) { 30.days.ago.to_date }
  let(:end_date) { Date.current }
  let!(:account) { create(:account) }

  before { Apartment::Tenant.switch!(account.tenant) }

  it "returns structured stats" do
    expect(result).to include(:totals, :conversion_funnel, :by_provider, :by_status, :credits, :period)
  end

  it "returns correct period" do
    expect(result[:period][:start_date]).to eq(start_date.to_s)
    expect(result[:period][:end_date]).to eq(end_date.to_s)
  end

  describe ":totals" do
    it "includes required keys" do
      expect(result[:totals]).to include(:total_sourced, :imported_to_candidates, :with_applies, :hired)
    end
  end

  describe ":conversion_funnel" do
    it "includes funnel stages" do
      expect(result[:conversion_funnel]).to include(:sourced_to_imported, :imported_to_applied, :applied_to_hired)
    end

    context "with no data" do
      it "returns zero rates" do
        expect(result[:conversion_funnel].values).to all(eq(0.0))
      end
    end
  end

  describe ":credits" do
    it "includes required keys" do
      expect(result[:credits]).to include(:total_consumed, :avg_cost_per_hire)
    end
  end
end
