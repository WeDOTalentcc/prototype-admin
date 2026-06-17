# frozen_string_literal: true

require "rails_helper"

RSpec.describe SourcedProfiles::ConvertToCandidateService do
  let(:account) { create(:account, ats_provider: "questt") }
  let(:user) { create(:user, account: account, is_admin: true) }

  let(:sourced_profile) do
    create(:sourced_profile,
           account: account,
           full_name: "John Doe",
           external_id: "linkedin123",
           email: nil,
           emails: [],
           candidate_id: nil)
  end

  describe "#call" do
    context "when sourced_profile has no email and account has ATS provider" do
      let(:enrichment_result) do
        {
          success: true,
          emails_found: true,
          phones_found: false,
          credits_used: 3
        }
      end

      before do
        allow(Pearch::ContactEnrichmentService).to receive(:new).and_return(
          instance_double(Pearch::ContactEnrichmentService, enrich!: enrichment_result)
        )
      end

      it "attempts to discover email via Pearch" do
        described_class.call([ sourced_profile.id ])

        expect(Pearch::ContactEnrichmentService).to have_received(:new).with(
          sourced_profile: sourced_profile,
          user: user,
          enrich_emails: true,
          enrich_phones: false,
          require_phones_or_emails: false
        )
      end

      it "creates candidate even if email discovery fails" do
        allow_any_instance_of(Pearch::ContactEnrichmentService)
          .to receive(:enrich!)
          .and_return({ success: false, error: "No credits" })

        result = described_class.call([ sourced_profile.id ])

        expect(result[:converted]).to eq(1)
        expect(result[:failed]).to eq(0)

        sourced_profile.reload
        expect(sourced_profile.candidate_id).to be_present
      end
    end

    context "when sourced_profile already has email" do
      let(:sourced_profile_with_email) do
        create(:sourced_profile,
               account: account,
               email: "john@example.com",
               external_id: "linkedin456",
               candidate_id: nil)
      end

      it "does not attempt email discovery" do
        allow(Pearch::ContactEnrichmentService).to receive(:new)

        described_class.call([ sourced_profile_with_email.id ])

        expect(Pearch::ContactEnrichmentService).not_to have_received(:new)
      end

      it "creates candidate with existing email" do
        result = described_class.call([ sourced_profile_with_email.id ])

        expect(result[:converted]).to eq(1)

        sourced_profile_with_email.reload
        candidate = Candidate.find(sourced_profile_with_email.candidate_id)

        expect(candidate.email).to eq("john@example.com")
      end
    end

    context "when account has no ATS provider" do
      let(:account_without_ats) { create(:account, ats_provider: nil) }
      let(:sourced_profile_no_ats) do
        create(:sourced_profile,
               account: account_without_ats,
               email: nil,
               external_id: "linkedin789",
               candidate_id: nil)
      end

      it "does not attempt email discovery" do
        allow(Pearch::ContactEnrichmentService).to receive(:new)

        described_class.call([ sourced_profile_no_ats.id ])

        expect(Pearch::ContactEnrichmentService).not_to have_received(:new)
      end

      it "creates candidate without email" do
        result = described_class.call([ sourced_profile_no_ats.id ])

        expect(result[:converted]).to eq(1)

        sourced_profile_no_ats.reload
        candidate = Candidate.find(sourced_profile_no_ats.candidate_id)

        expect(candidate.email).to be_blank
      end
    end

    context "when sourced_profile has no external_id" do
      let(:sourced_profile_no_external_id) do
        create(:sourced_profile,
               account: account,
               email: nil,
               external_id: nil,
               candidate_id: nil)
      end

      it "does not attempt email discovery" do
        allow(Pearch::ContactEnrichmentService).to receive(:new)

        described_class.call([ sourced_profile_no_external_id.id ])

        expect(Pearch::ContactEnrichmentService).not_to have_received(:new)
      end
    end

    context "when email discovery raises an error" do
      before do
        allow(Pearch::ContactEnrichmentService).to receive(:new)
          .and_raise(StandardError.new("Pearch API error"))
      end

      it "logs error but continues with conversion" do
        expect(Rails.logger).to receive(:error).with(/Email discovery error/)

        result = described_class.call([ sourced_profile.id ])

        expect(result[:converted]).to eq(1)
        expect(result[:failed]).to eq(0)
      end
    end

    context "multiple sourced profiles" do
      let(:sourced_profile_1) do
        create(:sourced_profile,
               account: account,
               email: nil,
               external_id: "linkedin001",
               candidate_id: nil)
      end

      let(:sourced_profile_2) do
        create(:sourced_profile,
               account: account,
               email: "existing@example.com",
               external_id: "linkedin002",
               candidate_id: nil)
      end

      it "handles mixed scenarios correctly" do
        allow(Pearch::ContactEnrichmentService).to receive(:new).and_call_original
        allow_any_instance_of(Pearch::ContactEnrichmentService)
          .to receive(:enrich!)
          .and_return({ success: false, error: "Test mode" })

        result = described_class.call([ sourced_profile_1.id, sourced_profile_2.id ])

        expect(result[:converted]).to eq(2)
        expect(Pearch::ContactEnrichmentService).to have_received(:new).once
      end
    end
  end

  describe "integration with ATS sync" do
    context "when candidate is created with pending applies" do
      let(:job) { create(:job, account: account) }
      let!(:apply) do
        create(:apply,
               account: account,
               candidate_id: nil,
               job: job,
               external_id: nil)
      end

      before do
        allow(AtsSync::ProcessApplyWithEnrichmentJob).to receive(:perform_in)
        allow_any_instance_of(Pearch::ContactEnrichmentService)
          .to receive(:enrich!)
          .and_return({ success: false, error: "Test" })
      end

      it "triggers ATS sync for pending applies" do
        described_class.call([ sourced_profile.id ])

        sourced_profile.reload
        candidate = Candidate.find(sourced_profile.candidate_id)

        apply.update(candidate_id: candidate.id)

        expect(AtsSync::ProcessApplyWithEnrichmentJob).to have_received(:perform_in)
      end
    end
  end
end
