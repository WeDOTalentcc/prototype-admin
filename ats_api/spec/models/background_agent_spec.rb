# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgent, type: :model do
  subject { build(:background_agent) }

  describe 'associations' do
    it { should belong_to(:job) }
    it { should belong_to(:user) }
    it { should belong_to(:account) }
    it { should have_many(:agent_cycles).dependent(:destroy) }
    it { should have_many(:agent_feedbacks).dependent(:destroy) }
    it { should have_many(:background_agent_steps).dependent(:destroy) }
  end

  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_inclusion_of(:status).in_array(BackgroundAgent::STATUSES) }
    it { should validate_inclusion_of(:calibration_state).in_array(BackgroundAgent::CALIBRATION_STATES) }
    it { should validate_inclusion_of(:mode).in_array(BackgroundAgent::MODES) }
    it { should validate_numericality_of(:daily_limit).is_greater_than(0) }
    it { should validate_numericality_of(:min_score_threshold).is_greater_than_or_equal_to(0).is_less_than_or_equal_to(100) }
  end

  describe 'scopes' do
    let!(:active_agent) { create(:background_agent, status: "active") }
    let!(:paused_agent) { create(:background_agent, :paused) }
    let!(:deleted_agent) { create(:background_agent, :deleted, status: "active") }

    it '.active excludes deleted and non-active' do
      expect(BackgroundAgent.active).to contain_exactly(active_agent)
    end

    it '.paused returns only paused non-deleted agents' do
      expect(BackgroundAgent.paused).to contain_exactly(paused_agent)
    end

    it '.runnable returns active agents that havent run today' do
      expect(BackgroundAgent.runnable).to include(active_agent)
    end

    it '.runnable excludes agents that ran today' do
      active_agent.update!(last_run_at: Time.current)
      expect(BackgroundAgent.runnable).not_to include(active_agent)
    end

    it '.by_job returns agents for a given job' do
      expect(BackgroundAgent.by_job(active_agent.job_id)).to contain_exactly(active_agent)
    end

    it '.calibrated returns calibrated agents' do
      calibrated_agent = create(:background_agent, :calibrated)
      expect(BackgroundAgent.calibrated).to include(calibrated_agent)
      expect(BackgroundAgent.calibrated).not_to include(active_agent)
    end
  end

  describe '#sync_sources_from_config' do
    let(:agent) { create(:background_agent, sources: ["local"]) }

    it "syncs sources from search_iteration_config on save" do
      agent.update!(search_iteration_config: { "enabled_providers" => ["local", "pearch", "linkedin"] })
      expect(agent.reload.sources).to eq(["local", "pearch", "linkedin"])
    end

    it "does not overwrite sources when config has no enabled_providers" do
      agent.update!(search_iteration_config: { "max_pages" => 5 })
      expect(agent.reload.sources).to eq(["local"])
    end
  end

  describe '#pause!' do
    let(:agent) { create(:background_agent) }

    it 'sets status to paused with timestamp' do
      agent.pause!
      expect(agent.status).to eq("paused")
      expect(agent.paused_at).to be_present
    end
  end

  describe '#resume!' do
    let(:agent) { create(:background_agent, :paused) }

    it 'sets status to active and clears paused_at' do
      agent.resume!
      expect(agent.status).to eq("active")
      expect(agent.paused_at).to be_nil
    end
  end

  describe '#stop!' do
    let(:agent) { create(:background_agent) }

    it 'sets status to stopped with timestamp' do
      agent.stop!
      expect(agent.status).to eq("stopped")
      expect(agent.stopped_at).to be_present
    end
  end

  describe '#approval_rate' do
    it 'returns 0.0 when no deliveries' do
      agent = build(:background_agent, total_delivered: 0)
      expect(agent.approval_rate).to eq(0.0)
    end

    it 'calculates correct rate' do
      agent = build(:background_agent, total_delivered: 20, total_approved: 15)
      expect(agent.approval_rate).to eq(75.0)
    end
  end

  describe '#remaining_today' do
    let(:agent) { create(:background_agent, daily_limit: 25) }

    it 'returns full limit when no cycles today' do
      expect(agent.remaining_today).to eq(25)
    end

    it 'subtracts todays delivered candidates' do
      sourcing = create(:sourcing, user: agent.user, account: agent.account)
      create(:agent_cycle, background_agent: agent, sourcing: sourcing, candidates_delivered: 10)
      expect(agent.remaining_today).to eq(15)
    end
  end

  describe '#should_auto_pause?' do
    it 'returns false when no interaction' do
      agent = build(:background_agent, last_interaction_at: nil)
      expect(agent.should_auto_pause?).to be false
    end

    it 'returns true when interaction is older than auto_pause_days' do
      agent = build(:background_agent, last_interaction_at: 5.days.ago, auto_pause_days: 4)
      expect(agent.should_auto_pause?).to be true
    end

    it 'returns false when interaction is recent' do
      agent = build(:background_agent, last_interaction_at: 1.day.ago, auto_pause_days: 4)
      expect(agent.should_auto_pause?).to be false
    end
  end

  describe '#log_search_iteration!' do
    let(:agent) { create(:background_agent) }

    it 'appends iteration data' do
      agent.log_search_iteration!(query_used: "ruby senior")
      expect(agent.search_history.size).to eq(1)
      expect(agent.search_history.last["query_used"]).to eq("ruby senior")
      expect(agent.search_history.last["timestamp"]).to be_present
    end

    it 'limits history to SEARCH_HISTORY_LIMIT entries' do
      agent.update!(search_history: Array.new(150) { { q: "old" } })
      agent.log_search_iteration!(query_used: "new")
      expect(agent.search_history.size).to eq(BackgroundAgent::SEARCH_HISTORY_LIMIT)
      expect(agent.search_history.last["query_used"]).to eq("new")
    end
  end

  describe '#next_cycle_number' do
    let(:agent) { create(:background_agent) }

    it 'returns 1 when no cycles exist' do
      expect(agent.next_cycle_number).to eq(1)
    end

    it 'returns next sequential number' do
      sourcing = create(:sourcing, user: agent.user, account: agent.account)
      create(:agent_cycle, background_agent: agent, sourcing: sourcing, cycle_number: 3)
      expect(agent.next_cycle_number).to eq(4)
    end
  end

  describe 'factory' do
    it 'is valid' do
      expect(build(:background_agent)).to be_valid
    end
  end
end
