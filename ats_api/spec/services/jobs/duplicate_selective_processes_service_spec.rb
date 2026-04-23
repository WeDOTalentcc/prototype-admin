# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::DuplicateSelectiveProcessesService do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  let!(:source_job) { create(:job, user: user, account: account) }
  let!(:target_job) { create(:job, user: user, account: account) }

  before do
    create(:selective_process, job: source_job, account: account, name: "Triagem", position: 0, status: :screening)
    create(:selective_process, job: source_job, account: account, name: "Entrevista", position: 1, status: :interview)
    create(:selective_process, job: source_job, account: account, name: "Contratado", position: 2, status: :hired)
  end

  describe '#call' do
    context 'when appending processes' do
      it 'copies selective processes from source to target' do
        result = described_class.new(
          target_job: target_job,
          source_job_id: source_job.id,
          replace: false
        ).call

        expect(result[:success]).to be true
        expect(target_job.selective_processes.where(is_deleted: false).count).to eq(3)
      end

      it 'preserves existing processes when appending' do
        create(:selective_process, job: target_job, account: account, name: "Existing", position: 0)

        result = described_class.new(
          target_job: target_job,
          source_job_id: source_job.id,
          replace: false
        ).call

        expect(result[:success]).to be true
        expect(target_job.selective_processes.where(is_deleted: false).count).to eq(4)
      end
    end

    context 'when replacing processes' do
      it 'soft deletes existing and copies new' do
        create(:selective_process, job: target_job, account: account, name: "Old Process", position: 0)

        result = described_class.new(
          target_job: target_job,
          source_job_id: source_job.id,
          replace: true
        ).call

        expect(result[:success]).to be true
        active_processes = target_job.selective_processes.where(is_deleted: false)
        expect(active_processes.count).to eq(3)
        expect(active_processes.pluck(:name)).not_to include("Old Process")
      end
    end

    context 'when source job does not exist' do
      it 'returns error' do
        result = described_class.new(
          target_job: target_job,
          source_job_id: 999999,
          replace: false
        ).call

        expect(result[:success]).to be false
        expect(result[:error]).to include("não encontrado")
      end
    end

    context 'when jobs belong to different accounts' do
      let!(:other_account) { create(:account) }
      let!(:other_user) { create(:user, account: other_account) }
      let!(:other_job) { create(:job, user: other_user, account: other_account) }

      it 'returns error' do
        result = described_class.new(
          target_job: target_job,
          source_job_id: other_job.id,
          replace: false
        ).call

        expect(result[:success]).to be false
        expect(result[:error]).to include("mesma conta")
      end
    end

    context 'when source has no processes' do
      let!(:empty_job) { create(:job, user: user, account: account) }

      it 'returns error' do
        result = described_class.new(
          target_job: target_job,
          source_job_id: empty_job.id,
          replace: false
        ).call

        expect(result[:success]).to be false
        expect(result[:error]).to include("não possui etapas")
      end
    end
  end
end
