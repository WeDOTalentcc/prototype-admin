require 'rails_helper'

RSpec.describe CandidateImportJob, type: :job do
  include ActiveJob::TestHelper

  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:data_file1) { create(:data_file, account: account) }
  let(:data_file2) { create(:data_file, account: account) }
  let(:data_file_ids) { [ data_file1.id, data_file2.id ] }

  describe '#perform' do
    let(:mock_candidate_data) do
      {
        basics: {
          name: 'João Silva'
        },
        skills: [ 'Ruby', 'Rails' ]
      }
    end

    before do
      # Mock dos serviços externos
      allow(RecruitAgentService).to receive(:extract_candidate_data).and_return(mock_candidate_data)

      # Mock do Yomu para extração de texto
      yomu_mock = instance_double(Yomu, text: 'Sample resume text')
      allow(Yomu).to receive(:new).and_return(yomu_mock)

      # Mock do ActionCable para broadcast
      allow(ActionCable.server).to receive(:broadcast)
    end

    context 'with valid parameters' do
      it 'processes all data files and broadcasts progress' do
        perform_enqueued_jobs do
          CandidateImportJob.perform_later(
            data_file_ids: data_file_ids,
            user_id: user.id
          )
        end

        # Verifica se os candidatos foram criados
        expect(Candidate.count).to eq(2)
        expect(Candidate.all.pluck(:account_id)).to all(eq(account.id))

        # Verifica broadcasts
        expect(ActionCable.server).to have_received(:broadcast).at_least(3).times

        # Verifica broadcast inicial
        expect(ActionCable.server).to have_received(:broadcast).with(
          "candidate_import_#{account.id}",
          hash_including(
            type: 'candidate_import_progress',
            data: hash_including(
              status: 'started',
              total: 2,
              processed: 0
            )
          )
        )

        # Verifica broadcast de conclusão
        expect(ActionCable.server).to have_received(:broadcast).with(
          "candidate_import_#{account.id}",
          hash_including(
            type: 'candidate_import_progress',
            data: hash_including(
              status: 'completed',
              total: 2,
              processed: 2,
              successful: 2,
              failed: 0
            )
          )
        )
      end

      it 'handles files without attachment' do
        allow(data_file1).to receive_message_chain(:file, :attached?).and_return(false)
        allow(DataFile).to receive(:where).and_return([ data_file1, data_file2 ])

        perform_enqueued_jobs do
          CandidateImportJob.perform_later(
            data_file_ids: data_file_ids,
            user_id: user.id
          )
        end

        # Apenas um candidato deve ser criado (data_file2)
        expect(Candidate.count).to eq(1)
      end

      it 'handles service extraction failures' do
        allow(RecruitAgentService).to receive(:extract_candidate_data).and_return(nil)

        perform_enqueued_jobs do
          CandidateImportJob.perform_later(
            data_file_ids: data_file_ids,
            user_id: user.id
          )
        end

        # Nenhum candidato deve ser criado
        expect(Candidate.count).to eq(0)

        # Deve broadcast com falhas
        expect(ActionCable.server).to have_received(:broadcast).with(
          "candidate_import_#{account.id}",
          hash_including(
            type: 'candidate_import_progress',
            data: hash_including(
              status: 'completed',
              failed: 2,
              successful: 0
            )
          )
        )
      end

      it 'handles text extraction failures' do
        yomu_mock = instance_double(Yomu, text: '')
        allow(Yomu).to receive(:new).and_return(yomu_mock)

        perform_enqueued_jobs do
          CandidateImportJob.perform_later(
            data_file_ids: data_file_ids,
            user_id: user.id
          )
        end

        expect(Candidate.count).to eq(0)
      end
    end

    context 'with invalid user_id' do
      it 'does not process files' do
        perform_enqueued_jobs do
          CandidateImportJob.perform_later(
            data_file_ids: data_file_ids,
            user_id: 999999
          )
        end

        expect(Candidate.count).to eq(0)
        expect(ActionCable.server).not_to have_received(:broadcast)
      end
    end

    context 'when exceptions occur' do
      before do
        allow(RecruitAgentService).to receive(:extract_candidate_data)
          .and_raise(StandardError.new('Service error'))
      end

      it 'handles exceptions gracefully and continues processing' do
        perform_enqueued_jobs do
          CandidateImportJob.perform_later(
            data_file_ids: data_file_ids,
            user_id: user.id
          )
        end

        # Verifica que o job não falhou completamente
        expect(ActionCable.server).to have_received(:broadcast).with(
          "candidate_import_#{account.id}",
          hash_including(
            type: 'candidate_import_progress',
            data: hash_including(
              status: 'completed',
              failed: 2
            )
          )
        )
      end
    end
  end

  describe 'private methods' do
    let(:job_instance) { CandidateImportJob.new }

    describe '#broadcast_progress' do
      it 'broadcasts progress data' do
        allow(ActionCable.server).to receive(:broadcast)

        progress_data = { status: 'processing', total: 5, processed: 2 }

        job_instance.send(:broadcast_progress, user, progress_data)

        expect(ActionCable.server).to have_received(:broadcast).with(
          "candidate_import_#{account.id}",
          hash_including(
            type: 'candidate_import_progress',
            data: progress_data,
            timestamp: kind_of(String)
          )
        )
      end
    end
  end
end
