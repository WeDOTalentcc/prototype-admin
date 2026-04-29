# frozen_string_literal: true

require "rails_helper"

RSpec.describe Evaluation, type: :model do
  let(:account) { create(:account, tenant: "public") }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:sp_screening) { create(:selective_process, job: job, account: account, status: :screening) }
  let(:sp_interview) { create(:selective_process, job: job, account: account, status: :interview) }

  before { Apartment::Tenant.switch!(account.tenant) }
  after { Apartment::Tenant.switch!("public") }

  describe ".screening scope" do
    it "returns evaluations with is_screening true" do
      screening_eval = create(:evaluation, job: job, selective_process: sp_screening, user: user, account: account, is_screening: true)
      create(:evaluation, job: job, selective_process: sp_interview, user: user, account: account, is_screening: false)

      expect(described_class.screening).to contain_exactly(screening_eval)
    end
  end

  describe "validate_screening_selective_process" do
    it "is valid when is_screening and selective_process has status screening" do
      evaluation = build(:evaluation, job: job, selective_process: sp_screening, user: user, account: account, is_screening: true)

      expect(evaluation).to be_valid
    end

    it "is invalid when is_screening but selective_process is not screening" do
      evaluation = build(:evaluation, job: job, selective_process: sp_interview, user: user, account: account, is_screening: true)

      expect(evaluation).not_to be_valid
      expect(evaluation.errors[:selective_process_id]).to include("must belong to a screening stage when is_screening is true")
    end

    it "is valid when is_screening false regardless of selective_process" do
      evaluation = build(:evaluation, job: job, selective_process: sp_interview, user: user, account: account, is_screening: false)

      expect(evaluation).to be_valid
    end
  end
end
