# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgents::SetupJob, type: :job do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job_record) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, user: user, account: account, job: job_record) }

  before do
    allow(RabbitMqPublisher).to receive(:publish)
  end

  describe '#perform' do
    it 'calls PublishToAgentService' do
      expect_any_instance_of(BackgroundAgents::PublishToAgentService).to receive(:call).and_return({ success: true })
      described_class.new.perform(agent.id, account.id)
    end

    it 'handles missing account' do
      expect { described_class.new.perform(agent.id, 999999) }.not_to raise_error
    end

    it 'handles missing agent' do
      expect { described_class.new.perform(999999, account.id) }.not_to raise_error
    end

    it 're-raises errors' do
      allow_any_instance_of(BackgroundAgents::PublishToAgentService).to receive(:call).and_raise(StandardError.new("boom"))
      expect { described_class.new.perform(agent.id, account.id) }.to raise_error(StandardError, "boom")
    end
  end
end
