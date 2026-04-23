# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::BulkAnalyticsService, type: :service do
  let(:account) { create(:account) }
  let!(:job1) { create(:job, account: account, is_active: true) }
  let!(:job2) { create(:job, account: account, is_active: true) }
  let!(:job3) { create(:job, account: account, is_deleted: true) }

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe '#call' do
    context 'with valid job ids' do
      subject(:result) { described_class.new(job_ids: [ job1.id, job2.id ]).call }

      it 'returns success' do
        expect(result[:success]).to be true
      end

      it 'returns analytics for each job' do
        expect(result[:data].keys).to contain_exactly(job1.id.to_s, job2.id.to_s)
      end

      it 'includes meta information' do
        expect(result[:meta][:requested_count]).to eq(2)
        expect(result[:meta][:found_count]).to eq(2)
      end

      it 'each job has overview data' do
        job_data = result[:data][job1.id.to_s]
        expect(job_data).to have_key(:overview)
        expect(job_data).to have_key(:funnel)
        expect(job_data).to have_key(:velocity)
      end
    end

    context 'with deleted job' do
      subject(:result) { described_class.new(job_ids: [ job1.id, job3.id ]).call }

      it 'excludes deleted job' do
        expect(result[:data].keys).to contain_exactly(job1.id.to_s)
      end
    end

    context 'with empty job ids' do
      subject(:result) { described_class.new(job_ids: []).call }

      it 'returns error' do
        expect(result[:success]).to be false
        expect(result[:error]).to be_present
      end
    end

    context 'with force refresh' do
      subject(:result) { described_class.new(job_ids: [ job1.id ], force_refresh: true).call }

      it 'bypasses cache' do
        expect_any_instance_of(Jobs::AnalyticsService).to receive(:call).and_call_original
        result
      end
    end
  end
end
