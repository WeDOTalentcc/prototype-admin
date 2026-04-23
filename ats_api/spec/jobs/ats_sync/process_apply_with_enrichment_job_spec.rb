# frozen_string_literal: true

require "rails_helper"

RSpec.describe AtsSync::ProcessApplyWithEnrichmentJob, type: :job do
  let(:account) { create(:account, ats_provider: "questt", tenant: "test_tenant") }
  let(:job_opening) { create(:job, account: account, external_id: "ext_job_123") }
  let(:selective_process) { create(:selective_process, job: job_opening, external_id: "ext_sp_123") }
  let(:candidate) { create(:candidate, account: account, name: "John Doe", linkedin: "https://linkedin.com/in/john-doe") }
  let(:apply) { create(:apply, candidate: candidate, job: job_opening, selective_process: selective_process, account: account) }

  before do
    allow(Apartment::Tenant).to receive(:switch).and_yield
    allow(AtsSync).to receive_message_chain(:config, :enabled?).and_return(true)
  end

  describe "#perform" do
    context "when candidate has no email and has LinkedIn" do
      before do
        candidate.update!(email: nil, linkedin: "https://linkedin.com/in/john-doe")
      end

      it "enriches email via Apify before syncing" do
        enrichment_service = instance_double(Candidates::LinkedinEnrichmentService)
        allow(Candidates::LinkedinEnrichmentService).to receive(:new).with(candidate).and_return(enrichment_service)

        result = instance_double(
          Candidates::LinkedinEnrichmentService::Result,
          success?: true,
          stats: { basic_fields: { updated: true, fields: [ :email ] } },
          error: nil
        )
        allow(enrichment_service).to receive(:call).and_return(result)

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)
        allow(candidate_service).to receive(:sync)

        apply_service = instance_double(AtsSync::ApplyService)
        allow(AtsSync::ApplyService).to receive(:new).and_return(apply_service)
        allow(apply_service).to receive(:sync)

        described_class.new.perform(apply.id, account.id)

        expect(enrichment_service).to have_received(:call)
        expect(candidate_service).to have_received(:sync)
        expect(apply_service).to have_received(:sync)
      end

      it "continues sync even if enrichment fails" do
        enrichment_service = instance_double(Candidates::LinkedinEnrichmentService)
        allow(Candidates::LinkedinEnrichmentService).to receive(:new).with(candidate).and_return(enrichment_service)
        allow(enrichment_service).to receive(:call).and_raise(StandardError.new("Apify error"))

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)
        allow(candidate_service).to receive(:sync)

        apply_service = instance_double(AtsSync::ApplyService)
        allow(AtsSync::ApplyService).to receive(:new).and_return(apply_service)
        allow(apply_service).to receive(:sync)

        described_class.new.perform(apply.id, account.id)

        expect(candidate_service).to have_received(:sync)
        expect(apply_service).to have_received(:sync)
      end

      it "continues sync when rate limit is hit" do
        enrichment_service = instance_double(Candidates::LinkedinEnrichmentService)
        allow(Candidates::LinkedinEnrichmentService).to receive(:new).with(candidate).and_return(enrichment_service)

        rate_limit_error = Apify::LinkedinProfileParserService::RateLimitError.new(
          "Rate limit",
          retry_after: Time.current + 1.hour
        )
        allow(enrichment_service).to receive(:call).and_raise(rate_limit_error)

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)
        allow(candidate_service).to receive(:sync)

        apply_service = instance_double(AtsSync::ApplyService)
        allow(AtsSync::ApplyService).to receive(:new).and_return(apply_service)
        allow(apply_service).to receive(:sync)

        described_class.new.perform(apply.id, account.id)

        expect(candidate_service).to have_received(:sync)
        expect(apply_service).to have_received(:sync)
      end
    end

    context "when candidate already has email" do
      before do
        candidate.update!(email: "john@example.com", linkedin: "https://linkedin.com/in/john-doe")
      end

      it "skips enrichment and syncs directly" do
        enrichment_service = instance_double(Candidates::LinkedinEnrichmentService)
        allow(Candidates::LinkedinEnrichmentService).to receive(:new).and_return(enrichment_service)

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)
        allow(candidate_service).to receive(:sync)

        apply_service = instance_double(AtsSync::ApplyService)
        allow(AtsSync::ApplyService).to receive(:new).and_return(apply_service)
        allow(apply_service).to receive(:sync)

        described_class.new.perform(apply.id, account.id)

        expect(enrichment_service).not_to have_received(:call)
        expect(candidate_service).to have_received(:sync)
        expect(apply_service).to have_received(:sync)
      end
    end

    context "when candidate has no LinkedIn" do
      before do
        candidate.update!(email: nil, linkedin: nil)
      end

      it "skips enrichment and syncs directly" do
        enrichment_service = instance_double(Candidates::LinkedinEnrichmentService)
        allow(Candidates::LinkedinEnrichmentService).to receive(:new).and_return(enrichment_service)

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)
        allow(candidate_service).to receive(:sync)

        apply_service = instance_double(AtsSync::ApplyService)
        allow(AtsSync::ApplyService).to receive(:new).and_return(apply_service)
        allow(apply_service).to receive(:sync)

        described_class.new.perform(apply.id, account.id)

        expect(enrichment_service).not_to have_received(:call)
        expect(candidate_service).to have_received(:sync)
        expect(apply_service).to have_received(:sync)
      end
    end

    context "when apply validation fails" do
      it "skips when candidate is missing" do
        apply.update_column(:candidate_id, nil)

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)

        described_class.new.perform(apply.id, account.id)

        expect(candidate_service).not_to have_received(:sync)
      end

      it "skips when job is missing" do
        apply.update_column(:job_id, nil)

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)

        described_class.new.perform(apply.id, account.id)

        expect(candidate_service).not_to have_received(:sync)
      end

      it "skips when account has no ats_provider" do
        account.update!(ats_provider: nil)

        candidate_service = instance_double(AtsSync::CandidateService)
        allow(AtsSync::CandidateService).to receive(:new).and_return(candidate_service)

        described_class.new.perform(apply.id, account.id)

        expect(candidate_service).not_to have_received(:sync)
      end
    end

    context "when apply is not found" do
      it "logs warning and does not raise error" do
        expect do
          described_class.new.perform(999999, account.id)
        end.not_to raise_error
      end
    end
  end
end
