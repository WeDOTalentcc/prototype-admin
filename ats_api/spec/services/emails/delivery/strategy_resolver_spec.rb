# frozen_string_literal: true

require "rails_helper"

RSpec.describe Emails::Delivery::StrategyResolver do
  describe ".for" do
    it "returns a MailgunStrategy for mailgun provider" do
      dispatch = double("Dispatch", provider: "mailgun")
      strategy = described_class.for(dispatch)
      expect(strategy).to be_a(Emails::Delivery::MailgunStrategy)
    end

    it "returns a MsGraphStrategy for ms_graph provider" do
      dispatch = double("Dispatch", provider: "ms_graph")
      strategy = described_class.for(dispatch)
      expect(strategy).to be_a(Emails::Delivery::MsGraphStrategy)
    end

    it "raises ArgumentError for unknown provider" do
      dispatch = double("Dispatch", provider: "unknown_provider")
      expect { described_class.for(dispatch) }.to raise_error(ArgumentError, /Unknown provider/)
    end
  end
end
