# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::PipelineHealthService, type: :service do
  let(:account) { create(:account) }
  let!(:job) { create(:job, account: account, is_active: true) }
  let!(:sp1) { create(:selective_process, job: job, name: "Triagem", position: 1, status: :screening) }
  let!(:sp2) { create(:selective_process, job: job, name: "Entrevista", position: 2, status: :interview) }
  let!(:sp3) { create(:selective_process, job: job, name: "Rejeitados", position: 3, status: :rejected) }
  let!(:candidate) { create(:candidate, account: account) }
  let!(:apply) { create(:apply, job: job, candidate: candidate, selective_process: sp1, account: account) }

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe '#call' do
    context 'with active jobs' do
      subject(:result) { described_class.new(job_ids: [ job.id ]).call }

      it 'returns success with data array' do
        expect(result[:success]).to be true
        expect(result[:data]).to be_an(Array)
        expect(result[:data].size).to eq(1)
      end

      it 'includes meta information' do
        expect(result[:meta][:total]).to eq(1)
        expect(result[:meta][:aging_threshold_days]).to eq(5)
        expect(result[:meta][:computed_at]).to be_present
      end

      it 'includes job basic info' do
        health = result[:data].first
        expect(health[:job_id]).to eq(job.id)
        expect(health[:title]).to eq(job.title)
        expect(health[:total_candidates]).to eq(1)
      end

      it 'includes stages health data' do
        health = result[:data].first
        expect(health[:by_stage]).to be_an(Array)
        expect(health[:by_stage].size).to eq(3)
      end

      it 'calculates conversion and rejection rates' do
        health = result[:data].first
        expect(health).to have_key(:conversion_rate)
        expect(health).to have_key(:rejection_rate)
      end

      it 'identifies bottleneck stage' do
        health = result[:data].first
        expect(health).to have_key(:bottleneck_stage)
      end

      it 'calculates health score' do
        health = result[:data].first
        expect(health[:health_score]).to be >= 0
      end
    end

    context 'with specific job ids' do
      let!(:job2) { create(:job, account: account, is_active: true) }

      subject(:result) { described_class.new(job_ids: [ job.id ]).call }

      it 'returns only specified jobs' do
        expect(result[:data].size).to eq(1)
        expect(result[:data].first[:job_id]).to eq(job.id)
      end
    end

    context 'with include_inactive flag' do
      let!(:inactive_job) { create(:job, account: account, is_active: false) }
      let!(:sp_inactive) { create(:selective_process, job: inactive_job, account: account, name: "Funil", status: :web_submission) }
      let!(:c_inactive) { create(:candidate, account: account) }
      let!(:a_inactive) { create(:apply, job: inactive_job, candidate: c_inactive, selective_process: sp_inactive, account: account) }

      subject(:result) { described_class.new(job_ids: [ job.id, inactive_job.id ], include_inactive: true).call }

      it 'includes inactive jobs' do
        job_ids = result[:data].map { |h| h[:job_id] }
        expect(job_ids).to include(inactive_job.id)
      end
    end

    context 'with job without candidates' do
      let!(:empty_job) { create(:job, account: account, is_active: true) }

      subject(:result) { described_class.new(job_ids: [ empty_job.id ]).call }

      it 'excludes jobs with zero candidates' do
        expect(result[:data]).to be_empty
      end
    end

    context 'with aging_threshold_days param' do
      subject(:result) { described_class.new(job_ids: [ job.id ], aging_threshold_days: 10).call }

      it 'uses custom threshold' do
        expect(result[:meta][:aging_threshold_days]).to eq(10)
      end
    end

    context 'with limit param' do
      let!(:job2) { create(:job, account: account, is_active: true) }
      let!(:sp_j2) { create(:selective_process, job: job2, account: account, name: "Funil", status: :web_submission) }
      let!(:c2) { create(:candidate, account: account) }
      let!(:a2) { create(:apply, job: job2, candidate: c2, selective_process: sp_j2, account: account) }

      subject(:result) { described_class.new(job_ids: [ job.id, job2.id ], limit: 1).call }

      it 'limits number of jobs processed' do
        expect(result[:data].size).to be <= 1
      end
    end
  end
end
