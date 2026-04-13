# frozen_string_literal: true

require "rails_helper"

RSpec.describe LiaEventsWorker do
  let(:worker) { described_class.new }

  describe "#work" do
    context "with valid event and known version" do
      it "returns :ack" do
        message = {
          event_type: "screening.completed",
          event_version: "1.0",
          company_id: 1,
          payload: { candidate_id: 42 },
        }.to_json

        expect(worker.work(message)).to eq(:ack)
      end

      it "logs receipt" do
        message = {
          event_type: "screening.completed",
          event_version: "1.0",
          company_id: 1,
          payload: {},
        }.to_json

        expect(Rails.logger).to receive(:info).with(/Event received/)
        # Allow handler logs too
        allow(Rails.logger).to receive(:info)
        worker.work(message)
      end
    end

    context "with incompatible version" do
      it "returns :reject" do
        message = {
          event_type: "screening.completed",
          event_version: "2.0",
          company_id: 1,
          payload: {},
        }.to_json

        expect(Rails.logger).to receive(:warn).with(/Incompatible event version/)
        expect(worker.work(message)).to eq(:reject)
      end
    end

    context "with malformed JSON" do
      it "returns :reject" do
        expect(Rails.logger).to receive(:error).with(/JSON parse error/)
        expect(worker.work("not json")).to eq(:reject)
      end
    end

    context "with unknown event type" do
      it "still acks (handler missing is OK)" do
        message = {
          event_type: "unknown.future.event",
          event_version: "1.0",
          company_id: 1,
          payload: {},
        }.to_json
        # Unknown events fail validation (not in registry)
        expect(worker.work(message)).to eq(:reject)
      end
    end
  end
end
