# frozen_string_literal: true

RSpec.describe PhoneCallInterviews::CreateService do
  subject(:result) { described_class.new(user: user, params: params).call }

  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:evaluation) { create(:evaluation, account: account) }
  let(:candidate) { create(:candidate, account: account, mobile_phone: "+5511999999999") }
  let(:job) { create(:job, account: account) }

  let(:params) do
    {
      evaluation_id: evaluation.id,
      candidate_id: candidate.id,
      job_id: job.id,
      custom_invite_message: "Olá, gostaríamos de conversar sobre a vaga!"
    }
  end

  before do
    Apartment::Tenant.switch!(account.tenant)
    allow(PhoneCallInterviews::InviteNotificationJob).to receive(:perform_later)
  end

  context "when all params are valid" do
    it "returns success" do
      expect(result.success?).to be true
    end

    it "creates a phone_call evaluation candidate" do
      expect { result }.to change(EvaluationCandidate, :count).by(1)
      ec = result.data
      expect(ec.evaluation_type).to eq("phone_call")
      expect(ec.phone_call_status).to eq("pending_schedule")
    end

    it "creates a scheduling link" do
      expect { result }.to change(SchedulingLink, :count).by(1)
      ec = result.data
      expect(ec.scheduling_link).to be_present
    end

    it "generates default scheduling slots" do
      result
      link = result.data.scheduling_link
      expect(link.scheduling_slots.count).to be > 0
    end

    it "dispatches invite notification" do
      result
      expect(PhoneCallInterviews::InviteNotificationJob).to have_received(:perform_later)
    end
  end

  context "when candidate has no phone" do
    let(:candidate) { create(:candidate, account: account, mobile_phone: nil) }

    it "returns failure" do
      expect(result.success?).to be false
      expect(result.errors).to include("Candidate has no phone number")
    end
  end

  context "when evaluation not found" do
    let(:params) { super().merge(evaluation_id: 999_999) }

    it "returns failure" do
      expect(result.success?).to be false
      expect(result.errors).to include("Evaluation not found")
    end
  end

  context "when candidate not found" do
    let(:params) { super().merge(candidate_id: 999_999) }

    it "returns failure" do
      expect(result.success?).to be false
      expect(result.errors).to include("Candidate not found")
    end
  end

  context "when job not found" do
    let(:params) { super().merge(job_id: 999_999) }

    it "returns failure" do
      expect(result.success?).to be false
      expect(result.errors).to include("Job not found")
    end
  end

  context "with custom slots" do
    let(:params) do
      super().merge(
        slots: [
          { start_time: 1.day.from_now.beginning_of_day + 10.hours, end_time: 1.day.from_now.beginning_of_day + 10.hours + 30.minutes },
          { start_time: 1.day.from_now.beginning_of_day + 11.hours, end_time: 1.day.from_now.beginning_of_day + 11.hours + 30.minutes }
        ]
      )
    end

    it "creates the specified slots" do
      result
      link = result.data.scheduling_link
      expect(link.scheduling_slots.count).to eq(2)
    end
  end
end
