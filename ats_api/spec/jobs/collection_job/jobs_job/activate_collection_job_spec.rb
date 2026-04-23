# frozen_string_literal: true

require 'rails_helper'

RSpec.describe CollectionJob::JobsJob::ActivateCollectionJob, type: :job do
  include ActiveJob::TestHelper

  describe '#perform' do
    let(:user_id) { 1 }
    let(:select_all_params) do
      {
        reference_type: 'Job',
        where: { is_active: false },
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

    let(:job_status_active) do
      instance_double(
        JobStatus,
        id: 1,
        name: 'Ativa'
      )
    end

    let(:job_status_paused) do
      instance_double(
        JobStatus,
        id: 2,
        name: 'Paralisada'
      )
    end

    let(:job1) do
      instance_double(
        Job,
        id: 101,
        is_deleted: false,
        update!: true
      )
    end

    let(:job2) do
      instance_double(
        Job,
        id: 102,
        is_deleted: false,
        update!: true
      )
    end

    let(:collection_result) do
      {
        records: [ job1, job2 ],
        total_count: 2
      }
    end

    before do
      stub_const('Current', Class.new { class << self; attr_accessor :user; end })

      allow(User).to receive(:find).with(user_id).and_return(user)
      allow(Apartment::Tenant).to receive(:switch!)
      allow(CollectionService).to receive(:call).and_return(collection_result)
      allow(CollectionChannel).to receive(:broadcast_to)
      allow_any_instance_of(described_class).to receive(:sleep)

      allow(JobStatus).to receive(:find_by).with(name: [ 'Ativa', 'Ativas' ]).and_return(job_status_active)
      allow(JobStatus).to receive(:find_by).with(name: [ 'Paralisada', 'Paralisadas' ]).and_return(job_status_paused)
    end

    context 'when activating jobs' do
      it 'processes activation and broadcasts progress' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(Apartment::Tenant).to have_received(:switch!).with('test_tenant')
        expect(CollectionService).to have_received(:call).at_least(:once)

        expect(job1).to have_received(:update!).with(
          hash_including(is_active: true, reason_for_pause: nil)
        )
        expect(job2).to have_received(:update!).with(
          hash_including(is_active: true, reason_for_pause: nil)
        )

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(status: 'loading')
        )

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(
            status: 'completed',
            percent: 100,
            message: /2 jobs activated successfully/
          )
        )
      end

      it 'updates job status when JobStatus exists' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(job1).to have_received(:update!).with(
          hash_including(job_status_id: job_status_active.id)
        )
      end
    end

    context 'when pausing jobs' do
      let(:reason_for_pause) { 'Budget exceeded' }

      it 'processes pause with reason' do
        perform_enqueued_jobs do
          described_class.perform_later(
            select_all_params,
            user_id,
            is_active: false,
            reason_for_pause: reason_for_pause
          )
        end

        expect(job1).to have_received(:update!).with(
          hash_including(
            is_active: false,
            reason_for_pause: reason_for_pause,
            job_status_id: job_status_paused.id
          )
        )

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(
            status: 'completed',
            message: /2 jobs paused successfully/
          )
        )
      end
    end

    context 'when job is deleted' do
      let(:deleted_job) do
        instance_double(
          Job,
          id: 103,
          is_deleted: true,
          update!: true
        )
      end

      let(:collection_with_deleted) do
        {
          records: [ job1, deleted_job, job2 ],
          total_count: 3
        }
      end

      before do
        allow(CollectionService).to receive(:call).and_return(collection_with_deleted)
        allow(deleted_job).to receive(:update!)
      end

      it 'skips deleted jobs' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(job1).to have_received(:update!)
        expect(job2).to have_received(:update!)
        expect(deleted_job).not_to have_received(:update!)

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(
            status: 'completed',
            message: /2 jobs activated successfully/
          )
        )
      end
    end

    context 'when processing multiple pages' do
      let(:job3) do
        instance_double(
          Job,
          id: 103,
          is_deleted: false,
          update!: true
        )
      end

      let(:first_page_result) do
        {
          records: [ job1, job2 ],
          total_count: 90
        }
      end

      let(:second_page_result) do
        {
          records: [ job3 ],
          total_count: 90
        }
      end

      let(:third_page_result) do
        {
          records: [],
          total_count: 90
        }
      end

      before do
        allow(CollectionService).to receive(:call)
          .with(select_all_params, 1).and_return(first_page_result)
        allow(CollectionService).to receive(:call)
          .with(select_all_params, 2).and_return(second_page_result)
        allow(CollectionService).to receive(:call)
          .with(select_all_params, 3).and_return(third_page_result)
      end

      it 'processes all pages' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(CollectionService).to have_received(:call).with(select_all_params, 1).at_least(:once)
        expect(CollectionService).to have_received(:call).with(select_all_params, 2)
        expect(CollectionService).to have_received(:call).with(select_all_params, 3)

        expect(job1).to have_received(:update!)
        expect(job2).to have_received(:update!)
        expect(job3).to have_received(:update!)
      end

      it 'broadcasts progress for each page' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(status: 'loading')
        ).at_least(3).times

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(status: 'completed', percent: 100)
        )
      end
    end

    context 'when update fails' do
      before do
        allow(job1).to receive(:update!).and_raise(StandardError.new('Update failed'))
        allow(Rails.logger).to receive(:error)
      end

      it 'logs error and continues processing' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(Rails.logger).to have_received(:error).with(
          /Error updating Job #101/
        )

        expect(job2).to have_received(:update!)

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(
            status: 'completed',
            message: /1 jobs activated successfully/
          )
        )
      end
    end

    context 'when collection is empty' do
      let(:empty_collection) do
        {
          records: [],
          total_count: 0
        }
      end

      before do
        allow(CollectionService).to receive(:call).and_return(empty_collection)
      end

      it 'completes without processing' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(
            status: 'completed',
            message: /0 jobs activated successfully/
          )
        )
      end
    end

    context 'when exception occurs' do
      let(:error_message) { 'Something went wrong' }

      before do
        allow(CollectionService).to receive(:call).and_raise(StandardError.new(error_message))
        allow(Rails.logger).to receive(:error)
      end

      it 'broadcasts error and re-raises' do
        expect {
          perform_enqueued_jobs do
            described_class.perform_later(select_all_params, user_id, is_active: true)
          end
        }.to raise_error

        expect(Rails.logger).to have_received(:error).with(
          /Error processing activation/
        )

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(
            status: 'error',
            message: /Error processing activation/
          )
        )
      end
    end

    context 'when JobStatus is not defined' do
      before do
        hide_const('JobStatus')
      end

      it 'processes without updating status' do
        perform_enqueued_jobs do
          described_class.perform_later(select_all_params, user_id, is_active: true)
        end

        expect(job1).to have_received(:update!).with(
          hash_not_including(:job_status_id)
        )

        expect(CollectionChannel).to have_received(:broadcast_to).with(
          "#{user_id}_collection",
          hash_including(
            status: 'completed',
            message: /2 jobs activated successfully$/
          )
        )
      end
    end
  end
end
