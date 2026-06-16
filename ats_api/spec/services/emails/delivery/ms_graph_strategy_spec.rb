# frozen_string_literal: true

require "rails_helper"

RSpec.describe Emails::Delivery::MsGraphStrategy do
  subject(:strategy) { described_class.new }

  let(:user)     { double("User", id: 1) }
  let(:dispatch) { double("Dispatch", user: user) }
  let(:message)  { double("DispatchMessage") }

  describe "#deliver" do
    it "delivers via MicrosoftService::Mailer and returns success hash" do
      allow(MicrosoftService::Mailer).to receive(:send_to_address).and_return({ id: "graph-msg-1" })

      result = strategy.deliver(
        to: "candidate@test.com",
        subject: "Opportunity",
        body: "<p>Hello</p>",
        dispatch: dispatch,
        message: message
      )

      expect(result[:success]).to be true
      expect(result[:provider]).to eq("ms_graph")
      expect(result[:response]).to eq({ id: "graph-msg-1" })
    end

    it "calls MicrosoftService::Mailer with correct params" do
      expect(MicrosoftService::Mailer).to receive(:send_to_address).with(
        user: user,
        to: "candidate@test.com",
        subject: "Opportunity",
        html: "<p>Hello</p>",
        save_to_sent: true
      ).and_return({})

      strategy.deliver(
        to: "candidate@test.com",
        subject: "Opportunity",
        body: "<p>Hello</p>",
        dispatch: dispatch,
        message: message
      )
    end
  end
end
