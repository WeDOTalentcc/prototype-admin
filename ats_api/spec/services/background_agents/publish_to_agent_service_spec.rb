# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgents::PublishToAgentService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, user: user, account: account, job: job) }

  before do
    allow(RabbitMqPublisher).to receive(:publish)
  end

  describe '#call' do
    context 'when agent is active with remaining quota' do
      it 'creates a sourcing and cycle' do
        expect { subject_call }.to change(AgentCycle, :count).by(1)
          .and change(Sourcing, :count).by(1)
      end

      it 'returns success with cycle info' do
        result = subject_call
        expect(result[:success]).to be true
        expect(result[:cycle_id]).to be_present
        expect(result[:cycle_number]).to eq(1)
      end

      it 'publishes to RabbitMQ' do
        subject_call
        expect(RabbitMqPublisher).to have_received(:publish).with(
          hash_including(
            exchange_name: "background_agents",
            routing_key: "background_agents.search"
          )
        )
      end

      it 'creates sourcing with background_agent provider' do
        subject_call
        sourcing = Sourcing.last
        expect(sourcing.provider).to eq("background_agent")
        expect(sourcing.parameters["background_agent_id"]).to eq(agent.id)
      end
    end

    context 'when agent is not active' do
      let(:agent) { create(:background_agent, :paused, user: user, account: account, job: job) }

      it 'returns error' do
        result = subject_call
        expect(result[:success]).to be false
        expect(result[:error]).to include("not active")
      end
    end

    context 'when no remaining quota' do
      before do
        sourcing = create(:sourcing, user: user, account: account)
        create(:agent_cycle, background_agent: agent, sourcing: sourcing, candidates_delivered: 25)
      end

      it 'returns error' do
        result = subject_call
        expect(result[:success]).to be false
        expect(result[:error]).to include("quota")
      end
    end
  end

  private

  def subject_call
    described_class.new(background_agent: agent).call
  end
end
