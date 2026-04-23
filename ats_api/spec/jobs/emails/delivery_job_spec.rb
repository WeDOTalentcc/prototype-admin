# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Emails::DeliveryJob, type: :job do
  let(:account) { double("Account", id: 1, tenant: "test_tenant") }
  let(:user) { double("User", id: 1, email: "recruiter@test.com") }
  let(:dispatch) { double("Dispatch", id: 1, provider: "mailgun", user_id: user.id, user: user, body: "Hello {{candidate_name}}", subject: "Job for {{candidate_name}}", account_id: account.id, account: account) }
  let(:message) { double("DispatchMessage", id: 1, dispatch: dispatch, recipient_address: "candidate@test.com", recipient_id: 1, account: account, update!: true) }
  let(:candidate) { double("Candidate", id: 1, name: "Test Candidate") }
  let(:record) { { candidate: { id: candidate.id, type: "Candidate" } }.to_json }

  before do
    allow(DispatchMessage).to receive_message_chain(:includes, :find).and_return(message)
    allow(Candidate).to receive(:find_by).with(id: 1).and_return(candidate)
    allow(Apartment::Tenant).to receive(:switch!).and_yield
    allow(Emails::RateLimiter).to receive(:check!)
    allow(Emails::CircuitBreaker).to receive(:check!)
    allow(Emails::RateLimiter).to receive(:record_send!)
    allow(Emails::CircuitBreaker).to receive(:record_success!)
  end

  it "checks rate limit before sending" do
    strategy = instance_double(Emails::Delivery::MailgunStrategy)
    allow(Emails::Delivery::StrategyResolver).to receive(:for).and_return(strategy)
    allow(strategy).to receive(:deliver).and_return({ success: true })

    expect(Emails::RateLimiter).to receive(:check!).ordered
    expect(strategy).to receive(:deliver).ordered

    described_class.new.perform(message.id, record)
  end

  it "replaces tags in body and subject" do
    strategy = instance_double(Emails::Delivery::MailgunStrategy)
    allow(Emails::Delivery::StrategyResolver).to receive(:for).and_return(strategy)

    expect(strategy).to receive(:deliver) do |**args|
      expect(args[:body]).to eq("Hello Test Candidate")
      expect(args[:subject]).to eq("Job for Test Candidate")
      { success: true }
    end

    described_class.new.perform(message.id, record)
  end

  it "updates status to sent on success" do
    strategy = instance_double(Emails::Delivery::MailgunStrategy)
    allow(Emails::Delivery::StrategyResolver).to receive(:for).and_return(strategy)
    allow(strategy).to receive(:deliver).and_return({ success: true })

    expect(message).to receive(:update!).with(status: :processing)
    expect(message).to receive(:update!).with(hash_including(status: :sent))

    described_class.new.perform(message.id, record)
  end

  it "updates status to failed on error" do
    strategy = instance_double(Emails::Delivery::MailgunStrategy)
    allow(Emails::Delivery::StrategyResolver).to receive(:for).and_return(strategy)
    allow(strategy).to receive(:deliver).and_raise(StandardError, "SMTP error")

    expect(message).to receive(:update!).with(hash_including(status: :failed))

    expect { described_class.new.perform(message.id, record) }.to raise_error(StandardError)
  end
end
