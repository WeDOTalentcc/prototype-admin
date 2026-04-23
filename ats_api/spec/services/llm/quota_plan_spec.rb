# frozen_string_literal: true

require "rails_helper"

RSpec.describe Llm::QuotaPlan do
  describe "PLANS" do
    it "defines starter, pro, and enterprise plans" do
      expect(described_class::PLANS.keys).to contain_exactly("starter", "pro", "enterprise")
    end

    it "has required keys for each plan" do
      described_class::PLANS.each_value do |config|
        expect(config).to include(:monthly_cost_limit_usd, :monthly_request_limit, :burst_rpm)
      end
    end
  end

  describe ".defaults_for" do
    it "returns starter defaults" do
      defaults = described_class.defaults_for("starter")
      expect(defaults[:monthly_cost_limit_usd]).to eq(5.00)
      expect(defaults[:monthly_request_limit]).to eq(5_000)
      expect(defaults[:burst_rpm]).to eq(20)
    end

    it "returns pro defaults" do
      defaults = described_class.defaults_for("pro")
      expect(defaults[:monthly_cost_limit_usd]).to eq(25.00)
    end

    it "returns enterprise defaults" do
      defaults = described_class.defaults_for("enterprise")
      expect(defaults[:monthly_cost_limit_usd]).to eq(100.00)
    end

    it "falls back to starter for unknown plan" do
      defaults = described_class.defaults_for("unknown")
      expect(defaults).to eq(described_class::PLANS["starter"])
    end
  end

  describe "DEFAULT_PLAN" do
    it "is starter" do
      expect(described_class::DEFAULT_PLAN).to eq("starter")
    end
  end
end
