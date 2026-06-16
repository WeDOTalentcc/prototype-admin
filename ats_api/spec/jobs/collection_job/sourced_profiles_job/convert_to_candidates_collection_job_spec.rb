# frozen_string_literal: true

require 'rails_helper'

RSpec.describe CollectionJob::SourcedProfilesJob::ConvertToCandidatesCollectionJob, type: :job do
  include ActiveJob::TestHelper

  describe '#perform' do
    let(:user_id) { 1 }
    let(:select_all_params) do
      {
        reference_type: 'SourcedProfileSourcing',
        where: { status: 'pending' },
        search: '*'
      }
    end

    let(:user) do
      instance_double(
        User,
        id: user_id,
        account: account
      )
    end

    let(:account) do
      instance_double(
        Account,
        id: 1,
        tenant: 'test_tenant'
      )
    end

    let(:sourced_profile1) do
      instance_double(
        SourcedProfile,
        id: 101,
        candidate_id: nil,
        is_deleted: false
      )
    end

    let(:sourced_profile2) do
      instance_double(
        SourcedProfile,
        id: 102,
        candidate_id: nil,
        is_deleted: false
      )
    end

    let(:sourced_profile_sourcing1) do
      instance_double(
        SourcedProfileSourcing,
        id: 1,
        is_deleted: false,
        sourced_profile: sourced_profile1
      )
    end

    let(:sourced_profile_sourcing2) do
      instance_double(
        SourcedProfileSourcing,
        id: 2,
        is_deleted: false,
        sourced_profile: sourced_profile2
      )
    end

    let(:collection_result) do
      {
        records: [ sourced_profile_sourcing1, sourced_profile_sourcing2 ],
        total_count: 2
      }
    end

    let(:conversion_result) do
      {
        converted: 2,
        skipped: 0,
        failed: 0,
        errors: []
      }
    end

    before do
      allow(User).to receive(:find).with(user_id).and_return(user)
      allow(Apartment::Tenant).to receive(:switch!)
      allow(CollectionService).to receive(:call).and_return(collection_result)
      allow(SourcedProfiles::ConvertToCandidateService).to receive(:call).and_return(conversion_result)
      allow(CollectionChannel).to receive(:broadcast_to)
      allow_any_instance_of(described_class).to receive(:sleep)
    end

    context 'com parâmetros válidos' do
      it 'processa conversão em lote e faz broadcast do progresso' do
        allow(sourced_profile_sourcing1).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(sourced_profile_sourcing2).to receive(:respond_to?).with(:sourced_profile).and_return(true)

        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id)
        end

        expect(Apartment::Tenant).to have_received(:switch!).with('test_tenant')

        expect(CollectionService).to have_received(:call).at_least(:once)

        expect(SourcedProfiles::ConvertToCandidateService).to have_received(:call)
          .with([ 101, 102 ])

        expect(CollectionChannel).to have_received(:broadcast_to)
          .with(
            "#{user_id}_collection",
            hash_including(status: 'loading')
          )

        expect(CollectionChannel).to have_received(:broadcast_to)
          .with(
            "#{user_id}_collection",
            hash_including(
              status: 'completed',
              percent: 100,
              converted: 2,
              failed: 0,
              skipped: 0
            )
          )
      end

      it 'pula registros deletados' do
        sourced_profile_deleted = instance_double(
          SourcedProfile,
          id: 103,
          candidate_id: nil
        )

        sourced_profile_sourcing_deleted = instance_double(
          SourcedProfileSourcing,
          id: 3,
          is_deleted: true,
          sourced_profile: sourced_profile_deleted
        )

        collection_with_deleted = {
          records: [ sourced_profile_sourcing1, sourced_profile_sourcing_deleted, sourced_profile_sourcing2 ],
          total_count: 3
        }

        allow(sourced_profile_sourcing1).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(sourced_profile_sourcing2).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(CollectionService).to receive(:call).and_return(collection_with_deleted)

        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id)
        end

        expect(SourcedProfiles::ConvertToCandidateService).to have_received(:call)
          .with([ 101, 102 ])
      end

      it 'pula sourced_profiles que já foram convertidos' do
        converted_profile = instance_double(
          SourcedProfile,
          id: 103,
          candidate_id: 999
        )

        sourced_profile_sourcing_converted = instance_double(
          SourcedProfileSourcing,
          id: 3,
          is_deleted: false,
          sourced_profile: converted_profile
        )

        collection_with_converted = {
          records: [ sourced_profile_sourcing1, sourced_profile_sourcing_converted, sourced_profile_sourcing2 ],
          total_count: 3
        }

        allow(sourced_profile_sourcing1).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(sourced_profile_sourcing2).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(sourced_profile_sourcing_converted).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(CollectionService).to receive(:call).and_return(collection_with_converted)

        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id)
        end

        expect(SourcedProfiles::ConvertToCandidateService).to have_received(:call)
          .with([ 101, 102 ])
      end
    end

    context 'quando há falhas na conversão' do
      let(:conversion_result_with_errors) do
        {
          converted: 1,
          skipped: 0,
          failed: 1,
          errors: [ { sourced_profile_id: 102, error: 'Validation failed' } ]
        }
      end

      before do
        allow(sourced_profile_sourcing1).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(sourced_profile_sourcing2).to receive(:respond_to?).with(:sourced_profile).and_return(true)

        allow(SourcedProfiles::ConvertToCandidateService).to receive(:call)
          .and_return(conversion_result_with_errors)
      end

      it 'registra falhas no log e continua processamento' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id)
        end

        expect(CollectionChannel).to have_received(:broadcast_to)
          .with(
            "#{user_id}_collection",
            hash_including(
              status: 'completed',
              converted: 1,
              failed: 1,
              skipped: 0
            )
          )
      end
    end

    context 'quando ocorre erro fatal' do
      before do
        allow(User).to receive(:find).and_raise(StandardError.new('User not found'))
      end

      it 'faz broadcast de erro e relança exceção' do
        expect {
          perform_enqueued_jobs do
            described_class.perform_later(select_all_params, user_id)
          end
        }.to raise_error

        expect(CollectionChannel).to have_received(:broadcast_to)
          .with(
            "#{user_id}_collection",
            hash_including(
              status: 'error',
              message: include('User not found')
            )
          )
      end
    end

    context 'processamento de múltiplas páginas' do
      let(:page1_result) do
        {
          records: [ sourced_profile_sourcing1 ],
          total_count: 40
        }
      end

      let(:page2_result) do
        {
          records: [ sourced_profile_sourcing2 ],
          total_count: 40
        }
      end

      before do
        allow(sourced_profile_sourcing1).to receive(:respond_to?).with(:sourced_profile).and_return(true)
        allow(sourced_profile_sourcing2).to receive(:respond_to?).with(:sourced_profile).and_return(true)

        allow(CollectionService).to receive(:call)
          .with(select_all_params, 1).and_return(page1_result)

        allow(CollectionService).to receive(:call)
          .with(select_all_params, 2).and_return(page2_result)
      end

      it 'processa todas as páginas sequencialmente' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id)
        end

        expect(CollectionService).to have_received(:call).with(select_all_params, 1)
        expect(CollectionService).to have_received(:call).with(select_all_params, 2)

        expect(SourcedProfiles::ConvertToCandidateService).to have_received(:call)
          .with([ 101 ])

        expect(SourcedProfiles::ConvertToCandidateService).to have_received(:call)
          .with([ 102 ])
      end
    end
  end
end
