# frozen_string_literal: true

require "rails_helper"

RSpec.describe MessagePublishJob, type: :job do
  let(:tenant) { "test_tenant" }

  describe "#perform" do
    it "switches tenant and calls execute_publish_event" do
      message = instance_double(Message)
      allow(Apartment::Tenant).to receive(:switch).with(tenant).and_yield
      allow(Message).to receive(:find_by).with(id: 1).and_return(message)
      allow(message).to receive(:execute_publish_event)

      described_class.new.perform(1, tenant)

      expect(message).to have_received(:execute_publish_event)
    end

    it "does nothing when message not found" do
      allow(Apartment::Tenant).to receive(:switch).with(tenant).and_yield
      allow(Message).to receive(:find_by).with(id: 999).and_return(nil)

      expect { described_class.new.perform(999, tenant) }.not_to raise_error
    end
  end
end
