# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgents::CronJob, type: :job do
  let(:account) { create(:account, is_active: true) }
  let(:user) { create(:user, account: account) }
  let(:job_record) { create(:job, user: user, account: account) }

  describe '#perform without account_id (dispatcher mode)' do
    it 'enqueues one job per active account' do
      create_list(:account, 3, is_active: true)
      inactive = create(:account, is_active: false)

      expect(BackgroundAgents::CronJob).to receive(:perform_async).at_least(3).times
      described_class.new.perform
    end
  end

  describe '#perform with account_id (worker mode)' do
    let!(:active_agent) { create(:background_agent, user: user, account: account, job: job_record) }

    before do
      allow(RabbitMqPublisher).to receive(:publish)
    end

    it 'processes runnable agents for the account' do
      described_class.new.perform(account.id)
      expect(RabbitMqPublisher).to have_received(:publish)
    end

    it 'auto-pauses stale agents' do
      active_agent.update!(last_interaction_at: 10.days.ago, auto_pause_days: 4)
      described_class.new.perform(account.id)
      expect(active_agent.reload.status).to eq("paused")
    end

    it 'skips agents that already ran today' do
      active_agent.update!(last_run_at: Time.current)
      described_class.new.perform(account.id)
      expect(RabbitMqPublisher).not_to have_received(:publish)
    end

    it 'handles missing account gracefully' do
      expect { described_class.new.perform(999999) }.not_to raise_error
    end

    it 'logs errors without raising' do
      allow(BackgroundAgent).to receive(:runnable).and_raise(StandardError.new("test error"))
      expect { described_class.new.perform(account.id) }.not_to raise_error
    end
  end
end
