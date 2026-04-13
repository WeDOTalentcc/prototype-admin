# frozen_string_literal: true

require "rails_helper"

RSpec.describe LiaEvents::EventPublisher do
  let(:publisher) { described_class.new(rabbitmq_url: "amqp://guest:guest@localhost:5672") }

  describe "#publish" do
    context "with unknown event type" do
      it "returns false and logs warning without connecting" do
        expect(Rails.logger).to receive(:warn).with(/Unknown event_type/)
        result = publisher.publish(event_type: "unknown.event", company_id: 1, payload: {})
        expect(result).to be false
      end
    end

    context "with known event type but RabbitMQ unavailable" do
      it "returns false and logs warning (fail-open)" do
        allow(Bunny).to receive(:new).and_raise(StandardError, "Connection refused")
        expect(Rails.logger).to receive(:warn).with(/Publish failed/)
        result = publisher.publish(event_type: "screening.completed", company_id: 1, payload: {})
        expect(result).to be false
      end
    end

    context "envelope structure" do
      let(:mock_connection) { double("Bunny::Session") }
      let(:mock_channel) { double("Bunny::Channel") }
      let(:mock_exchange) { double("Bunny::Exchange") }

      before do
        allow(Bunny).to receive(:new).and_return(mock_connection)
        allow(mock_connection).to receive(:start)
        allow(mock_connection).to receive(:create_channel).and_return(mock_channel)
        allow(mock_connection).to receive(:close)
        allow(mock_channel).to receive(:direct).and_return(mock_exchange)
      end

      it "includes event_version in published envelope" do
        expect(mock_exchange).to receive(:publish) do |json, _opts|
          parsed = JSON.parse(json)
          expect(parsed["event_type"]).to eq("screening.completed")
          expect(parsed["event_version"]).to eq("1.0")
          expect(parsed["source"]).to eq("rails-ats-api")
          expect(parsed["company_id"]).to eq(42)
          expect(parsed["payload"]).to eq("candidate_id" => 123)
        end

        publisher.publish(
          event_type: "screening.completed",
          company_id: 42,
          payload: { candidate_id: 123 }
        )
      end
    end
  end
end
