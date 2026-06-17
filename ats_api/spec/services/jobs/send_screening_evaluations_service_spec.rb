# frozen_string_literal: true

require "rails_helper"

RSpec.describe Jobs::SendScreeningEvaluationsService do
  let(:account) { create(:account, tenant: "public") }
  let(:user) { create(:user, account: account) }
  let(:job) do
    create(:job, user: user, account: account, is_screening_active: true,
                 web_saturation_amount: 2, sourcing_saturation_amount: 3)
  end
  let(:sp_screening) do
    create(:selective_process, job: job, account: account, name: "Triagem",
                              position: 1, status: :screening)
  end
  let(:evaluation) do
    create(:evaluation, job: job, selective_process: sp_screening, user: user,
                        account: account, is_screening: true, is_trigger: true)
  end

  before do
    allow(Jobs::SendScreeningEvaluationsJob).to receive(:perform_async)
    Apartment::Tenant.switch!(account.tenant)
    sp_screening
    evaluation
  end

  after { Apartment::Tenant.switch!("public") }

  describe ".call" do
    context "when job has no screening active" do
      before { job.update!(is_screening_active: false) }

      it "returns error and does not send" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be false
        expect(result[:error]).to include("screening not active")
        expect(result[:sent_count]).to eq(0)
      end
    end

    context "when job has no screening stage" do
      before { sp_screening.update_column(:status, SelectiveProcess.statuses[:web_submission]) }

      it "returns error" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be false
        expect(result[:error]).to include("No screening stage")
      end
    end

    context "when job has no screening evaluation" do
      before { evaluation.update!(is_screening: false) }

      it "returns error" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be false
        expect(result[:error]).to include("No screening evaluation")
      end
    end

    context "when allowed_screenings_limit_date has passed" do
      before { job.update!(allowed_screenings_limit_date: 1.hour.ago) }

      it "returns error and does not send" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be false
        expect(result[:error]).to include("Screening send limit date reached")
        expect(result[:sent_count]).to eq(0)
      end
    end

    context "when allowed_screenings_limit_date is in the future" do
      before { job.update!(allowed_screenings_limit_date: 1.hour.from_now) }

      it "does not return screening limit date error" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:error].to_s).not_to include("Screening send limit date reached")
      end
    end

    context "when applies exist in screening stage" do
      let(:candidate1) { create(:candidate, account: account) }
      let(:candidate2) { create(:candidate, account: account) }
      let!(:apply1) do
        create(:apply, job: job, candidate: candidate1, selective_process: sp_screening,
               account: account, source: "web_response", is_screening_sent: false)
      end
      let!(:apply2) do
        create(:apply, job: job, candidate: candidate2, selective_process: sp_screening,
               account: account, source: "sourcing", is_screening_sent: false)
      end

      it "creates EvaluationCandidate and sets is_screening_sent" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be true
        expect(result[:sent_count]).to eq(2)
        expect(result[:skipped_saturation]).to eq(0)

        expect(EvaluationCandidate.exists?(apply_id: apply1.id, evaluation_id: evaluation.id)).to be true
        expect(EvaluationCandidate.exists?(apply_id: apply2.id, evaluation_id: evaluation.id)).to be true
        expect(apply1.reload.is_screening_sent).to be true
        expect(apply2.reload.is_screening_sent).to be true
      end
    end

    context "when saturation limit is reached for web" do
      let(:candidate1) { create(:candidate, account: account) }
      let(:candidate2) { create(:candidate, account: account) }
      let(:candidate3) { create(:candidate, account: account) }
      let!(:apply1) do
        create(:apply, job: job, candidate: candidate1, selective_process: sp_screening,
               account: account, source: "web_response", is_screening_sent: false, created_at: 3.days.ago)
      end
      let!(:apply2) do
        create(:apply, job: job, candidate: candidate2, selective_process: sp_screening,
               account: account, source: "web_response", is_screening_sent: false, created_at: 2.days.ago)
      end
      let!(:apply3) do
        create(:apply, job: job, candidate: candidate3, selective_process: sp_screening,
               account: account, source: "web_response", is_screening_sent: false, created_at: 1.day.ago)
      end

      before { job.update!(web_saturation_amount: 2) }

      it "sends to first 2 web applies and skips the 3rd" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be true
        expect(result[:sent_count]).to eq(2)
        expect(result[:skipped_saturation]).to eq(1)

        expect(apply1.reload.is_screening_sent).to be true
        expect(apply2.reload.is_screening_sent).to be true
        expect(apply3.reload.is_screening_sent).to be false
      end
    end

    context "when saturation limit is reached for sourcing" do
      let(:candidates) { create_list(:candidate, 4, account: account) }
      let!(:applies) do
        candidates.each_with_index.map do |c, i|
          create(:apply, job: job, candidate: c, selective_process: sp_screening,
                 account: account, source: "sourcing", is_screening_sent: false,
                 created_at: (4 - i).days.ago)
        end
      end

      before { job.update!(sourcing_saturation_amount: 3) }

      it "sends to first 3 sourcing applies and skips the 4th" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be true
        expect(result[:sent_count]).to eq(3)
        expect(result[:skipped_saturation]).to eq(1)

        expect(applies[0].reload.is_screening_sent).to be true
        expect(applies[1].reload.is_screening_sent).to be true
        expect(applies[2].reload.is_screening_sent).to be true
        expect(applies[3].reload.is_screening_sent).to be false
      end
    end

    context "when apply already has EvaluationCandidate" do
      let(:candidate1) { create(:candidate, account: account) }
      let!(:apply1) do
        create(:apply, job: job, candidate: candidate1, selective_process: sp_screening,
               account: account, source: "web_response", is_screening_sent: false)
      end

      before do
        create(:evaluation_candidate, evaluation: evaluation, candidate: candidate1,
               apply: apply1, job: job, user: user, account: account)
      end

      it "does not create duplicate EvaluationCandidate" do
        expect { described_class.call(job_id: job.id, account_id: account.id) }
          .not_to change(EvaluationCandidate, :count)
      end
    end

    context "when apply already has is_screening_sent true" do
      let(:candidate1) { create(:candidate, account: account) }
      let!(:apply1) do
        create(:apply, job: job, candidate: candidate1, selective_process: sp_screening,
               account: account, source: "web_response", is_screening_sent: true)
      end

      it "does not process apply again" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be true
        expect(result[:sent_count]).to eq(0)
        expect(EvaluationCandidate.exists?(apply_id: apply1.id, evaluation_id: evaluation.id)).to be false
      end
    end

    context "when multiple applies web + sourcing and either limit blocks all" do
      let(:web_candidates) { create_list(:candidate, 2, account: account) }
      let(:sourcing_candidates) { create_list(:candidate, 4, account: account) }
      let!(:web_applies) do
        web_candidates.each_with_index.map do |c, i|
          create(:apply, job: job, candidate: c, selective_process: sp_screening,
                 account: account, source: "web_response", is_screening_sent: false,
                 created_at: (6 - i).days.ago)
        end
      end
      let!(:sourcing_applies) do
        sourcing_candidates.each_with_index.map do |c, i|
          create(:apply, job: job, candidate: c, selective_process: sp_screening,
                 account: account, source: "sourcing", is_screening_sent: false,
                 created_at: (4 - i).days.ago)
        end
      end

      before do
        job.update!(web_saturation_amount: 2, sourcing_saturation_amount: 3)
      end

      it "blocks all sends when either source reaches its limit" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be true
        expect(result[:sent_count]).to eq(2)
        expect(result[:skipped_saturation]).to eq(4)

        web_applies.each { |a| expect(a.reload.is_screening_sent).to be true }
        sourcing_applies.each { |a| expect(a.reload.is_screening_sent).to be false }
      end
    end

    context "when allowed_screenings_limit_date is active, saturation is overridden" do
      let(:web_candidates) { create_list(:candidate, 2, account: account) }
      let(:sourcing_candidates) { create_list(:candidate, 4, account: account) }
      let!(:web_applies) do
        web_candidates.each_with_index.map do |c, i|
          create(:apply, job: job, candidate: c, selective_process: sp_screening,
                 account: account, source: "web_response", is_screening_sent: false,
                 created_at: (6 - i).days.ago)
        end
      end
      let!(:sourcing_applies) do
        sourcing_candidates.each_with_index.map do |c, i|
          create(:apply, job: job, candidate: c, selective_process: sp_screening,
                 account: account, source: "sourcing", is_screening_sent: false,
                 created_at: (4 - i).days.ago)
        end
      end

      before do
        job.update!(
          web_saturation_amount: 2,
          sourcing_saturation_amount: 3,
          allowed_screenings_limit_date: 1.hour.from_now
        )
      end

      it "sends to all applies ignoring saturation when limit date is active" do
        result = described_class.call(job_id: job.id, account_id: account.id)

        expect(result[:success]).to be true
        expect(result[:sent_count]).to eq(6)
        expect(result[:skipped_saturation]).to eq(0)

        web_applies.each { |a| expect(a.reload.is_screening_sent).to be true }
        sourcing_applies.each { |a| expect(a.reload.is_screening_sent).to be true }
      end
    end
  end

  describe "Job#default_user_id_for_screening" do
    it "returns evaluation user_id when present" do
      expect(job.default_user_id_for_screening(evaluation: evaluation)).to eq(user.id)
    end

    it "returns job user_id when evaluation has no user" do
      evaluation.update_column(:user_id, nil)
      expect(job.default_user_id_for_screening(evaluation: evaluation)).to eq(user.id)
    end

    it "returns account admin when job has no user" do
      job.update_column(:user_id, nil)
      evaluation.update_column(:user_id, nil)
      admin = create(:user, account: account, is_admin: true)

      expect(job.default_user_id_for_screening(evaluation: evaluation)).to eq(admin.id)
    end
  end

  describe "Job#can_send_screenings?" do
    it "returns true when allowed_screenings_limit_date is nil" do
      job.update_column(:allowed_screenings_limit_date, nil)
      expect(job.can_send_screenings?).to be true
    end

    it "returns true when allowed_screenings_limit_date is in the future" do
      job.update!(allowed_screenings_limit_date: 1.hour.from_now)
      expect(job.can_send_screenings?).to be true
    end

    it "returns false when allowed_screenings_limit_date has passed" do
      job.update!(allowed_screenings_limit_date: 1.hour.ago)
      expect(job.can_send_screenings?).to be false
    end
  end

  describe "Job.within_screening_send_window" do
    it "includes jobs with nil allowed_screenings_limit_date" do
      job.update_column(:allowed_screenings_limit_date, nil)
      expect(Job.within_screening_send_window).to include(job)
    end

    it "includes jobs with allowed_screenings_limit_date in the future" do
      job.update!(allowed_screenings_limit_date: 1.hour.from_now)
      expect(Job.within_screening_send_window).to include(job)
    end

    it "excludes jobs with allowed_screenings_limit_date in the past" do
      job.update!(allowed_screenings_limit_date: 1.hour.ago)
      expect(Job.within_screening_send_window).not_to include(job)
    end
  end

  describe "Job#saturation_limit_for_source" do
    it "returns web_saturation_amount for web_response" do
      expect(job.saturation_limit_for_source("web_response")).to eq(2)
    end

    it "returns web_saturation_amount for web" do
      expect(job.saturation_limit_for_source("web")).to eq(2)
    end

    it "returns sourcing_saturation_amount for sourcing" do
      expect(job.saturation_limit_for_source("sourcing")).to eq(3)
    end

    it "returns sourcing_saturation_amount for unknown source" do
      expect(job.saturation_limit_for_source("unknown")).to eq(3)
    end
  end

  describe "Job#effective_saturation_limit_for_source" do
    it "returns base limit when saturation_amount_increase is 0" do
      job.update!(saturation_amount_increase: 0, saturation_release_hours: 24)
      expect(job.effective_saturation_limit_for_source("web", first_sent_at: 25.hours.ago)).to eq(2)
    end

    it "returns base limit when saturation_release_hours is 0" do
      job.update!(saturation_amount_increase: 1, saturation_release_hours: 0)
      expect(job.effective_saturation_limit_for_source("web", first_sent_at: 25.hours.ago)).to eq(2)
    end

    it "returns base limit when first_sent_at is nil" do
      job.update!(saturation_amount_increase: 1, saturation_release_hours: 24)
      expect(job.effective_saturation_limit_for_source("web", first_sent_at: nil)).to eq(2)
    end

    it "returns base + increase when one release period has elapsed" do
      job.update!(
        web_saturation_amount: 2,
        saturation_amount_increase: 1,
        saturation_release_hours: 24
      )
      expect(job.effective_saturation_limit_for_source("web", first_sent_at: 25.hours.ago)).to eq(3)
    end

    it "returns base + 2*increase when two release periods have elapsed" do
      job.update!(
        web_saturation_amount: 2,
        saturation_amount_increase: 1,
        saturation_release_hours: 24
      )
      expect(job.effective_saturation_limit_for_source("web", first_sent_at: 50.hours.ago)).to eq(4)
    end

    it "returns base when less than one period has elapsed" do
      job.update!(
        web_saturation_amount: 2,
        saturation_amount_increase: 1,
        saturation_release_hours: 24
      )
      expect(job.effective_saturation_limit_for_source("web", first_sent_at: 12.hours.ago)).to eq(2)
    end
  end

  context "when saturation_amount_increase and saturation_release_hours are set" do
    let(:candidates) { create_list(:candidate, 5, account: account) }
    let!(:applies) do
      candidates.each_with_index.map do |c, i|
        create(:apply, job: job, candidate: c, selective_process: sp_screening,
               account: account, source: "web_response", is_screening_sent: false,
               created_at: (5 - i).days.ago)
      end
    end

    before do
      job.update!(
        web_saturation_amount: 2,
        saturation_amount_increase: 1,
        saturation_release_hours: 24
      )
    end

    it "sends to first 2, then after 25h cron sends to 3rd (limit increased)" do
      result = described_class.call(job_id: job.id, account_id: account.id)

      expect(result[:success]).to be true
      expect(result[:sent_count]).to eq(2)
      expect(result[:skipped_saturation]).to eq(3)

      expect(applies[0].reload.is_screening_sent).to be true
      expect(applies[1].reload.is_screening_sent).to be true
      expect(applies[2].reload.is_screening_sent).to be false
      expect(applies[3].reload.is_screening_sent).to be false

      first_ec = EvaluationCandidate.find_by(apply_id: applies[0].id, evaluation_id: evaluation.id)
      first_ec.update_column(:created_at, 25.hours.ago)

      result2 = described_class.call(job_id: job.id, account_id: account.id)

      expect(result2[:success]).to be true
      expect(result2[:sent_count]).to eq(1)
      expect(result2[:skipped_saturation]).to eq(2)
      expect(applies[2].reload.is_screening_sent).to be true
    end
  end

  describe "user_id resolution" do
    let(:candidate) { create(:candidate, account: account) }
    let!(:apply) do
      create(:apply, job: job, candidate: candidate, selective_process: sp_screening,
             account: account, source: "web_response", is_screening_sent: false)
    end

    it "uses explicit user_id when provided" do
      other_user = create(:user, account: account)
      job.update_column(:user_id, nil)
      evaluation.update_column(:user_id, nil)

      result = described_class.call(job_id: job.id, account_id: account.id, user_id: other_user.id)

      expect(result[:success]).to be true
      expect(EvaluationCandidate.last.user_id).to eq(other_user.id)
    end

    it "falls back to evaluation.user_id when no explicit user_id" do
      result = described_class.call(job_id: job.id, account_id: account.id)

      expect(result[:success]).to be true
      expect(EvaluationCandidate.last.user_id).to eq(user.id)
    end
  end
end
