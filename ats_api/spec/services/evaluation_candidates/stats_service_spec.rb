# frozen_string_literal: true

require "rails_helper"

RSpec.describe EvaluationCandidates::StatsService do
  subject(:result) { described_class.new(start_date: start_date, end_date: end_date).call }

  let(:start_date) { 30.days.ago.to_date }
  let(:end_date) { Date.current }
  let!(:account) { create(:account) }

  before { Apartment::Tenant.switch!(account.tenant) }

  it "returns structured stats" do
    expect(result).to include(:totals, :completion_rate, :avg_score, :score_distribution, :by_classification, :screening_stats, :period)
  end

  it "returns correct period" do
    expect(result[:period][:start_date]).to eq(start_date.to_s)
    expect(result[:period][:end_date]).to eq(end_date.to_s)
  end

  describe ":totals" do
    it "includes required keys" do
      expect(result[:totals]).to include(:total_sent, :completed, :pending, :expired)
    end
  end

  describe ":screening_stats" do
    it "includes required keys" do
      expect(result[:screening_stats]).to include(:total_screening, :pass_rate, :auto_advanced)
    end
  end
end
