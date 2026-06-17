# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgents::ProcessFeedbackService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, user: user, account: account, job: job, calibration_state: "pending") }
  let(:sourcing) { create(:sourcing, user: user, account: account) }
  let(:cycle) { create(:agent_cycle, background_agent: agent, sourcing: sourcing, status: "running", candidates_delivered: 2) }

  let(:sps1) { create(:sourced_profile_sourcing, account: account, user: user) }
  let(:sps2) { create(:sourced_profile_sourcing, account: account, user: user) }

  before do
    allow(BackgroundAgents::ExtractPreferencesJob).to receive(:perform_async)
  end

  describe '#call' do
    context 'with empty feedbacks' do
      it 'returns error' do
        result = described_class.new(background_agent: agent, feedbacks: []).call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("No feedbacks provided")
      end
    end

    context 'with valid feedbacks' do
      let(:feedbacks) do
        [
          { sourced_profile_sourcing_id: sps1.id, agent_cycle_id: cycle.id, action: "approved" },
          { sourced_profile_sourcing_id: sps2.id, agent_cycle_id: cycle.id, action: "rejected", reason: "Too junior" }
        ]
      end

      it 'creates feedback records' do
        expect {
          described_class.new(background_agent: agent, feedbacks: feedbacks).call
        }.to change(AgentFeedback, :count).by(2)
      end

      it 'updates counters atomically' do
        described_class.new(background_agent: agent, feedbacks: feedbacks).call
        agent.reload
        expect(agent.total_approved).to eq(1)
        expect(agent.total_rejected).to eq(1)
      end

      it 'updates last_interaction_at' do
        described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(agent.reload.last_interaction_at).to be_present
      end

      it 'transitions calibration from pending to learning' do
        described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(agent.reload.calibration_state).to eq("learning")
      end

      it 'returns success with state info' do
        result = described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(result[:success]).to be true
        expect(result[:processed]).to eq(2)
        expect(result[:calibration_state]).to be_present
      end
    end

    context 'calibration threshold' do
      let(:agent) { create(:background_agent, user: user, account: account, job: job, calibration_state: "learning", total_approved: 3, total_rejected: 1) }

      it 'calibrates when threshold reached' do
        feedbacks = [{ sourced_profile_sourcing_id: sps1.id, agent_cycle_id: cycle.id, action: "approved" }]
        described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(agent.reload.calibration_state).to eq("calibrated")
      end

      it 'enqueues ExtractPreferencesJob on calibration' do
        feedbacks = [{ sourced_profile_sourcing_id: sps1.id, agent_cycle_id: cycle.id, action: "approved" }]
        described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(BackgroundAgents::ExtractPreferencesJob).to have_received(:perform_async)
      end
    end

    context 'duplicate feedback' do
      it 'silently skips duplicates' do
        create(:agent_feedback, background_agent: agent, agent_cycle: cycle, sourced_profile_sourcing: sps1)
        feedbacks = [{ sourced_profile_sourcing_id: sps1.id, agent_cycle_id: cycle.id, action: "approved" }]

        result = described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(result[:success]).to be true
        expect(result[:processed]).to eq(0)
      end
    end

    context 'cycle review completion' do
      before do
        allow(BackgroundAgentChannel).to receive(:broadcast_to)
      end

      it 'marks cycle as reviewed when all candidates get feedback' do
        feedbacks = [
          { sourced_profile_sourcing_id: sps1.id, agent_cycle_id: cycle.id, action: "approved" },
          { sourced_profile_sourcing_id: sps2.id, agent_cycle_id: cycle.id, action: "rejected", reason: "No fit" }
        ]
        described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(cycle.reload.status).to eq("reviewed")
      end
    end

    context "sync_candidate_feedback" do
      let(:feedbacks) do
        [{ sourced_profile_sourcing_id: sps1.id, agent_cycle_id: cycle.id, action: "approved" }]
      end

      it "calls CandidateFeedbacks::UpsertService with skip_agent_sync" do
        allow(CandidateFeedbacks::UpsertService).to receive(:call).and_return({ success: true })

        described_class.new(background_agent: agent, feedbacks: feedbacks).call

        expect(CandidateFeedbacks::UpsertService).to have_received(:call).with(
          hash_including(
            sourced_profile_sourcing_id: sps1.id,
            user: user,
            feedback_type: "like",
            skip_agent_sync: true
          )
        )
      end

      it "does not fail when UpsertService raises" do
        allow(CandidateFeedbacks::UpsertService).to receive(:call).and_raise(StandardError, "sync error")

        result = described_class.new(background_agent: agent, feedbacks: feedbacks).call
        expect(result[:success]).to be true
        expect(result[:processed]).to eq(1)
      end

      it "maps rejected action to dislike feedback_type" do
        allow(CandidateFeedbacks::UpsertService).to receive(:call).and_return({ success: true })

        rejected_feedbacks = [{ sourced_profile_sourcing_id: sps1.id, agent_cycle_id: cycle.id, action: "rejected", reason: "No fit" }]
        described_class.new(background_agent: agent, feedbacks: rejected_feedbacks).call

        expect(CandidateFeedbacks::UpsertService).to have_received(:call).with(
          hash_including(feedback_type: "dislike", reason: "No fit")
        )
      end
    end
  end
end
