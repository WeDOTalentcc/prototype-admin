# frozen_string_literal: true

require "rails_helper"

RSpec.describe Emails::BatchDispatchService do
  let(:sender) { double("User", id: 1, account_id: 10) }
  let(:recipients) do
    [
      { email: "a@test.com", candidate_id: 1, name: "Alice" },
      { email: "b@test.com", candidate_id: 2, name: "Bob" }
    ]
  end
  let(:template) { "Hello {{candidate_name}}" }
  let(:subject_line) { "Job offer" }

  before do
    allow(Emails::OrchestratorJob).to receive(:perform_async)
  end

  describe ".call" do
    context "with valid inputs" do
      it "creates a dispatch and returns a successful result" do
        dispatch = instance_double(Dispatch, id: 99)
        allow(Dispatch).to receive(:create!).and_return(dispatch)

        result = described_class.call(
          recipients: recipients,
          template: template,
          subject: subject_line,
          sender: sender
        )

        expect(result.success).to be true
        expect(result.dispatch).to eq(dispatch)
        expect(result.errors).to be_empty
      end

      it "enqueues OrchestratorJob with dispatch id and payloads" do
        dispatch = instance_double(Dispatch, id: 42)
        allow(Dispatch).to receive(:create!).and_return(dispatch)

        described_class.call(
          recipients: recipients,
          template: template,
          subject: subject_line,
          sender: sender
        )

        expect(Emails::OrchestratorJob).to have_received(:perform_async).with(
          42,
          anything,
          anything
        )
      end

      it "serializes recipients correctly in payload" do
        dispatch = instance_double(Dispatch, id: 1)
        allow(Dispatch).to receive(:create!).and_return(dispatch)

        captured_payload = nil
        allow(Emails::OrchestratorJob).to receive(:perform_async) do |_, recipients_json, _|
          captured_payload = JSON.parse(recipients_json, symbolize_names: true)
        end

        described_class.call(
          recipients: recipients,
          template: template,
          subject: subject_line,
          sender: sender
        )

        expect(captured_payload.first[:email]).to eq("a@test.com")
        expect(captured_payload.first[:candidate_id]).to eq(1)
      end
    end

    context "with invalid inputs" do
      it "raises ArgumentError when recipients is empty" do
        expect do
          described_class.call(
            recipients: [],
            template: template,
            subject: subject_line,
            sender: sender
          )
        end.to raise_error(ArgumentError, /cannot be empty/)
      end

      it "raises ArgumentError when template is blank" do
        expect do
          described_class.call(
            recipients: recipients,
            template: "",
            subject: subject_line,
            sender: sender
          )
        end.to raise_error(ArgumentError, /cannot be blank/)
      end

      it "raises ArgumentError when recipients exceeds 50000" do
        large_list = Array.new(50_001) { { email: "x@test.com", candidate_id: 1, name: "X" } }

        expect do
          described_class.call(
            recipients: large_list,
            template: template,
            subject: subject_line,
            sender: sender
          )
        end.to raise_error(ArgumentError, /exceeds maximum/)
      end

      it "returns failed result when Dispatch.create! raises RecordInvalid" do
        dispatch = Dispatch.new
        allow(Dispatch).to receive(:create!).and_raise(ActiveRecord::RecordInvalid.new(dispatch))

        result = described_class.call(
          recipients: recipients,
          template: template,
          subject: subject_line,
          sender: sender
        )

        expect(result.success).to be false
        expect(result.dispatch).to be_nil
        expect(result.errors).not_to be_empty
      end
    end
  end
end
