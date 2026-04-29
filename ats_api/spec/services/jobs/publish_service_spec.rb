# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::PublishService do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  before do
    JobStatus.create_default_statuses
    allow(Current).to receive(:user).and_return(user)
    allow(Current).to receive(:ip).and_return('127.0.0.1')
  end

  let(:active_status) { JobStatus.find_by(name: "Ativa") }
  let(:draft_status) { JobStatus.find_by(name: "Rascunho") }

  describe '#publish' do
    context 'when job is ready for publication' do
      let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

      before do
        checker = instance_double(Jobs::FieldRequirementChecker, is_ready_for_publication?: true)
        allow(Jobs::FieldRequirementChecker).to receive(:new).and_return(checker)
      end

      it 'publishes the job' do
        result = described_class.new(job: job).publish

        expect(result[:success]).to be true
        expect(job.reload.published_date).to be_present
        expect(job.is_active).to be true
        expect(job.job_status).to eq(active_status)
      end
    end

    context 'when job is not ready for publication' do
      let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

      before do
        missing = [ { field: "salary_from", category: "critical" } ]
        checker = instance_double(
          Jobs::FieldRequirementChecker,
          is_ready_for_publication?: false,
          make_missing_fields: missing
        )
        allow(Jobs::FieldRequirementChecker).to receive(:new).and_return(checker)
      end

      it 'returns error with missing fields' do
        result = described_class.new(job: job).publish

        expect(result[:success]).to be false
        expect(result[:error]).to include("não está pronta")
        expect(result[:missing_fields]).to be_present
      end
    end
  end

  describe '#unpublish' do
    let!(:job) { create(:job, user: user, account: account, job_status: active_status, published_date: Time.current, is_active: true) }

    it 'unpublishes the job' do
      result = described_class.new(job: job).unpublish

      expect(result[:success]).to be true
      expect(job.reload.published_date).to be_nil
      expect(job.is_active).to be false
      expect(job.job_status).to eq(draft_status)
    end
  end
end
