# frozen_string_literal: true

require "rails_helper"

RSpec.describe Evaluations::ResponseRatesService, type: :service do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let!(:job) { create(:job, account: account, user: user, is_active: true) }
  let!(:sp) { create(:selective_process, job: job, account: account, name: "Funil", status: :web_submission) }
  let!(:evaluation) { create(:evaluation, account: account, user: user, job: job, selective_process: sp, is_deleted: false) }

  let!(:candidate1) { create(:candidate, account: account) }
  let!(:candidate2) { create(:candidate, account: account) }
  let!(:candidate3) { create(:candidate, account: account) }

  let!(:apply1) { create(:apply, job: job, candidate: candidate1, selective_process: sp, account: account) }

  let!(:ec_completed) do
    create(:evaluation_candidate,
           evaluation: evaluation, candidate: candidate1, account: account,
           user: user, job: job, apply: apply1,
           completed: true, score: 85)
  end

  let!(:ec_completed2) do
    create(:evaluation_candidate,
           evaluation: evaluation, candidate: candidate2, account: account,
           user: user, job: job,
           completed: true, score: 72)
  end

  let!(:ec_pending) do
    create(:evaluation_candidate,
           evaluation: evaluation, candidate: candidate3, account: account,
           user: user, job: job,
           completed: false)
  end

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe "#call" do
    context "with default params" do
      subject(:result) { described_class.new(evaluation_ids: [ evaluation.id ]).call }

      it "returns success" do
        expect(result[:success]).to be true
      end

      it "returns stats for all evaluations" do
        expect(result[:data].size).to eq(1)
      end

      it "calculates response rate correctly" do
        stats = result[:data].first
        expect(stats[:total_sent]).to eq(3)
        expect(stats[:total_completed]).to eq(2)
        expect(stats[:total_pending]).to eq(1)
        expect(stats[:response_rate]).to eq(66.67)
      end

      it "calculates average score" do
        stats = result[:data].first
        expect(stats[:avg_score]).to eq(78.5)
      end

      it "includes evaluation info" do
        stats = result[:data].first
        expect(stats[:evaluation_id]).to eq(evaluation.id)
        expect(stats[:evaluation_name]).to eq(evaluation.name)
        expect(stats[:job_id]).to eq(job.id)
        expect(stats[:job_title]).to eq(job.title)
      end

      it "includes meta with overall stats" do
        meta = result[:meta]
        expect(meta[:total_evaluations]).to eq(1)
        expect(meta[:overall_response_rate]).to be_a(Float)
        expect(meta[:computed_at]).to be_present
      end
    end

    context "with evaluation_ids filter" do
      let!(:evaluation2) { create(:evaluation, account: account, user: user, job: job, selective_process: sp, is_deleted: false) }

      subject(:result) { described_class.new(evaluation_ids: [ evaluation.id ]).call }

      it "returns only specified evaluations" do
        expect(result[:data].size).to eq(1)
        expect(result[:data].first[:evaluation_id]).to eq(evaluation.id)
      end
    end

    context "with job_ids filter" do
      let!(:other_job) { create(:job, account: account, user: user, is_active: true) }
      let!(:other_sp) { create(:selective_process, job: other_job, account: account, name: "Funil", status: :web_submission) }
      let!(:other_eval) { create(:evaluation, account: account, user: user, job: other_job, selective_process: other_sp, is_deleted: false) }

      subject(:result) { described_class.new(job_ids: [ other_job.id ]).call }

      it "filters by job" do
        expect(result[:data].size).to eq(1)
        expect(result[:data].first[:job_id]).to eq(other_job.id)
      end
    end

    context "with include_pending" do
      subject(:result) { described_class.new(evaluation_ids: [ evaluation.id ], include_pending: true).call }

      it "includes pending candidates list" do
        stats = result[:data].first
        expect(stats[:pending_candidates]).to be_an(Array)
        expect(stats[:pending_candidates].size).to eq(1)
      end

      it "includes pending candidate details" do
        pending = result[:data].first[:pending_candidates].first
        expect(pending[:candidate_id]).to eq(candidate3.id)
        expect(pending[:candidate_name]).to eq(candidate3.name)
        expect(pending[:sent_at]).to be_present
      end
    end

    context "with min_rate filter" do
      subject(:result) { described_class.new(evaluation_ids: [ evaluation.id ], min_rate: 90).call }

      it "excludes evaluations below min rate" do
        expect(result[:data]).to be_empty
      end
    end

    context "with max_rate filter" do
      subject(:result) { described_class.new(evaluation_ids: [ evaluation.id ], max_rate: 50).call }

      it "excludes evaluations above max rate" do
        expect(result[:data]).to be_empty
      end
    end

    context "when no evaluations exist" do
      subject(:result) { described_class.new(evaluation_ids: [ 0 ]).call }

      it "returns empty result" do
        expect(result[:success]).to be true
        expect(result[:data]).to be_empty
      end
    end

    context "when evaluation has no sent candidates" do
      let!(:empty_eval) { create(:evaluation, account: account, user: user, job: job, selective_process: sp, is_deleted: false) }

      subject(:result) { described_class.new(evaluation_ids: [ empty_eval.id ]).call }

      it "returns zero response rate" do
        stats = result[:data].first
        expect(stats[:total_sent]).to eq(0)
        expect(stats[:response_rate]).to eq(0.0)
      end
    end
  end
end
