# frozen_string_literal: true

require "rails_helper"

RSpec.describe MessageService::EventPublisher do
  let(:connection) { instance_double("Bunny::Session") }
  let(:channel)    { instance_double("Bunny::Channel") }
  let(:exchange)   { instance_double("Bunny::Exchange") }
  let(:pool)       { instance_double("ConnectionPool") }

  before do
    allow(described_class).to receive(:connection_pool).and_return(pool)
    allow(pool).to receive(:with).and_yield(connection)
    allow(connection).to receive(:create_channel).and_return(channel)
    allow(channel).to receive(:direct).and_return(exchange)
    allow(exchange).to receive(:publish)
    allow(channel).to receive(:close)
  end

  def build_payload(question_text:, candidate_answer:, job_description:)
    {
      account_id: 41,
      message_id: 11,
      evaluation_candidate_id: 22,
      question_id: 33,
      question_text: question_text,
      candidate_answer: candidate_answer,
      job_description: job_description
    }
  end

  context "when publishing to evaluations exchange" do
    it "publishes with correct exchange and routing key" do
      payload = build_payload(
        question_text: "Explain Sidekiq vs Active Job",
        candidate_answer: "Active Job is the unified interface; Sidekiq is an adapter backed by Redis.",
        job_description: "Ruby on Rails, Sidekiq, Redis"
      )

      result = described_class.publish(
        payload,
        exchange_name: "evaluations_exchange",
        routing_key: "evaluation_request"
      )

      expect(pool).to have_received(:with)
      expect(connection).to have_received(:create_channel)
      expect(channel).to have_received(:direct).with("evaluations_exchange", durable: true)
      expect(exchange).to have_received(:publish).with(
        payload.to_json,
        routing_key: "evaluation_request",
        persistent: true
      )

      expect(result).to include(
        status: :ok,
        payload: payload,
        exchange_name: "evaluations_exchange",
        routing_key: "evaluation_request",
        message_id: payload[:message_id]
      )
    end
  end

  context "when using defaults" do
    it "publishes to messages_exchange with messages_created routing key" do
      payload = build_payload(
        question_text: "Difference between includes and joins?",
        candidate_answer: "joins creates INNER JOIN; includes does eager loading.",
        job_description: "Rails, ActiveRecord"
      )

      described_class.publish(payload)

      expect(channel).to have_received(:direct).with("messages_exchange", durable: true)
      expect(exchange).to have_received(:publish).with(
        payload.to_json,
        routing_key: "messages_created",
        persistent: true
      )
    end
  end

  context "when connection fails and retries" do
    before do
      call_count = 0
      allow(pool).to receive(:with) do |&block|
        call_count += 1
        raise Bunny::TCPConnectionFailed.new("", "") if call_count <= 2
        block.call(connection)
      end
      allow(described_class).to receive(:reset_pool!)
      allow(described_class).to receive(:sleep)
    end

    it "retries and eventually succeeds" do
      payload = build_payload(
        question_text: "Test retry",
        candidate_answer: "Answer",
        job_description: "Rails"
      )

      result = described_class.publish(payload)

      expect(result[:status]).to eq(:ok)
      expect(described_class).to have_received(:reset_pool!).twice
    end
  end
end
