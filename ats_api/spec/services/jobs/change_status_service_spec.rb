# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::ChangeStatusService do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  before do
    JobStatus.create_default_statuses
    allow(Current).to receive(:user).and_return(user)
    allow(Current).to receive(:ip).and_return('127.0.0.1')
  end

  let(:active_status) { JobStatus.find_by(name: "Ativa") }
  let(:draft_status) { JobStatus.find_by(name: "Rascunho") }
  let(:paused_status) { JobStatus.find_by(name: "Paralisada") }
  let(:cancelled_status) { JobStatus.find_by(name: "Cancelada") }
  let(:closed_status) { JobStatus.find_by(name: "Fechada (preenchida)") }
  let(:reopened_status) { JobStatus.find_by(name: "Reaberta") }
  let(:archived_status) { JobStatus.find_by(name: "Arquivada") }
  let(:completed_status) { JobStatus.find_by(name: "Concluída") }

  describe '#call' do
    context 'when transition is allowed' do
      let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

      it 'transitions from Rascunho to Ativa' do
        result = described_class.new(job: job, target_status_id: active_status.id).call

        expect(result[:success]).to be true
        expect(job.reload.job_status).to eq(active_status)
        expect(job.is_active).to be true
      end

      it 'transitions from Ativa to Paralisada with reason' do
        job.update!(job_status: active_status)

        result = described_class.new(
          job: job,
          target_status_id: paused_status.id,
          reason: "Budget review"
        ).call

        expect(result[:success]).to be true
        expect(job.reload.job_status).to eq(paused_status)
        expect(job.reason_for_pause).to eq("Budget review")
        expect(job.is_active).to be false
      end

      it 'transitions from Ativa to Concluída' do
        job.update!(job_status: active_status)

        result = described_class.new(job: job, target_status_id: completed_status.id).call

        expect(result[:success]).to be true
        expect(job.reload.job_status).to eq(completed_status)
      end

      it 'sets is_archived when transitioning to Arquivada' do
        job.update!(job_status: closed_status)

        result = described_class.new(job: job, target_status_id: archived_status.id).call

        expect(result[:success]).to be true
        expect(job.reload.is_archived).to be true
      end

      it 'sets is_active true when transitioning to Reaberta' do
        job.update!(job_status: closed_status)

        result = described_class.new(job: job, target_status_id: reopened_status.id).call

        expect(result[:success]).to be true
        expect(job.reload.is_active).to be true
      end
    end

    context 'when transition is not allowed' do
      let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

      it 'rejects Rascunho to Fechada (preenchida)' do
        result = described_class.new(job: job, target_status_id: closed_status.id).call

        expect(result[:success]).to be false
        expect(result[:error]).to include("Transição não permitida")
        expect(result[:allowed_transitions]).to be_present
      end

      it 'rejects Arquivada to Ativa' do
        job.update!(job_status: archived_status)

        result = described_class.new(job: job, target_status_id: active_status.id).call

        expect(result[:success]).to be false
      end
    end

    context 'when target status does not exist' do
      let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

      it 'returns error' do
        result = described_class.new(job: job, target_status_id: 999999).call

        expect(result[:success]).to be false
        expect(result[:error]).to include("não encontrado")
      end
    end

    context 'activity log' do
      let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

      it 'creates activity log entry on status change' do
        expect {
          described_class.new(job: job, target_status_id: active_status.id).call
        }.to change(ActivityLog, :count)
      end
    end
  end
end
