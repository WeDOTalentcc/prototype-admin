# frozen_string_literal: true

require "rails_helper"

RSpec.describe Emails::Delivery::MailgunStrategy do
  subject(:strategy) { described_class.new }

  let(:dispatch) { double("Dispatch", user: double("User", email: "sender@company.com")) }
  let(:message)  { double("DispatchMessage") }
  let(:mail_message) { double("Mail::Message", message_id: "abc123@mailgun") }

  describe "#deliver" do
    it "delivers via DispatchMailer and returns success hash" do
      allow(DispatchMailer).to receive(:send_email).and_return(mail_message)
      allow(mail_message).to receive(:deliver_now).and_return(mail_message)

      result = strategy.deliver(
        to: "candidate@test.com",
        subject: "Opportunity",
        body: "Hello",
        dispatch: dispatch,
        message: message
      )

      expect(result[:success]).to be true
      expect(result[:provider]).to eq("mailgun")
      expect(result[:message_id]).to eq("abc123@mailgun")
    end

    it "uses dispatch user email as sender" do
      allow(DispatchMailer).to receive(:send_email).and_return(mail_message)
      allow(mail_message).to receive(:deliver_now).and_return(mail_message)

      expect(DispatchMailer).to receive(:send_email).with(
        hash_including(from: "sender@company.com")
      )

      strategy.deliver(
        to: "x@test.com",
        subject: "S",
        body: "B",
        dispatch: dispatch,
        message: message
      )
    end

    it "falls back to DEFAULT_FROM_EMAIL when user is nil" do
      dispatch_no_user = double("Dispatch", user: nil)
      allow(DispatchMailer).to receive(:send_email).and_return(mail_message)
      allow(mail_message).to receive(:deliver_now).and_return(mail_message)

      expect(DispatchMailer).to receive(:send_email).with(
        hash_including(from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc"))
      )

      strategy.deliver(
        to: "x@test.com",
        subject: "S",
        body: "B",
        dispatch: dispatch_no_user,
        message: message
      )
    end
  end
end
