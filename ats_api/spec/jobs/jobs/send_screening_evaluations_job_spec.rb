# frozen_string_literal: true

require "rails_helper"

RSpec.describe Jobs::SendScreeningEvaluationsJob do
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
  let(:candidate) { create(:candidate, account: account) }
  let!(:apply) do
    create(:apply, job: job, candidate: candidate, selective_process: sp_screening,
           account: account, source: "web_response", is_screening_sent: false)
  end

  before do
    Apartment::Tenant.switch!(account.tenant)
    sp_screening
    evaluation
  end

  after { Apartment::Tenant.switch!("public") }

  describe "#perform" do
    it "calls the service and creates EvaluationCandidate" do
      expect {
        described_class.new.perform(job.id, account.id)
      }.to change(EvaluationCandidate, :count).by(1)

      expect(apply.reload.is_screening_sent).to be true
    end

    it "does nothing when account is not found" do
      expect(Jobs::SendScreeningEvaluationsService).not_to receive(:call)

      described_class.new.perform(job.id, 0)
    end

    it "switches tenant before calling service" do
      expect(Apartment::Tenant).to receive(:switch).with(account.tenant).and_call_original

      described_class.new.perform(job.id, account.id)
    end
  end
end
