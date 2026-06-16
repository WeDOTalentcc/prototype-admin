# frozen_string_literal: true

require "rails_helper"

# GAP-10-004: Ensure LGPD candidate cleanup job anonymizes expired records.
RSpec.describe LgpdCandidateCleanupJob, type: :job do
  describe "#perform" do
    let!(:expired_candidate) do
      create(:candidate,
             name: "Candidato LGPD Test",
             email: "lgpd@test.com",
             cpf: "12345678901",
             lgpd_expires_at: 2.days.ago)
    end

    let!(:active_candidate) do
      create(:candidate,
             name: "Candidato Ativo",
             email: "ativo@test.com",
             lgpd_expires_at: 30.days.from_now)
    end

    let!(:no_expiry_candidate) do
      create(:candidate,
             name: "Candidato Sem Expiracao",
             lgpd_expires_at: nil)
    end

    it "anonymizes candidates with expired lgpd_expires_at" do
      described_class.perform_now

      expired_candidate.reload
      expect(expired_candidate.name).to eq(LgpdCandidateCleanupJob::ANONYMIZED_SENTINEL)
      expect(expired_candidate.email).to be_nil
      expect(expired_candidate.cpf).to be_nil
    end

    it "does not touch candidates with future lgpd_expires_at" do
      described_class.perform_now

      active_candidate.reload
      expect(active_candidate.name).to eq("Candidato Ativo")
      expect(active_candidate.email).to eq("ativo@test.com")
    end

    it "does not touch candidates with nil lgpd_expires_at" do
      described_class.perform_now

      no_expiry_candidate.reload
      expect(no_expiry_candidate.name).to eq("Candidato Sem Expiracao")
    end

    it "in dry_run mode does not modify records" do
      described_class.perform_now(dry_run: true)

      expired_candidate.reload
      expect(expired_candidate.name).to eq("Candidato LGPD Test")
      expect(expired_candidate.email).to eq("lgpd@test.com")
    end

    it "clears lgpd_expires_at after anonymization" do
      described_class.perform_now

      expired_candidate.reload
      expect(expired_candidate.lgpd_expires_at).to be_nil
    end
  end
end
