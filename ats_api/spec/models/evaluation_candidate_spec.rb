# frozen_string_literal: true

require 'rails_helper'

RSpec.describe EvaluationCandidate, type: :model do
  subject { build(:evaluation_candidate) }

  it { should belong_to(:evaluation) }
  it { should belong_to(:candidate) }
  it { should belong_to(:account) }
  it { should belong_to(:user).optional }
  it { should belong_to(:job).optional }
  it { should belong_to(:apply).optional }

  it { should validate_presence_of(:evaluation) }
  it { should validate_presence_of(:candidate) }
  it { should validate_presence_of(:account) }

  it 'has a valid factory' do
    expect(build(:evaluation_candidate)).to be_valid
  end

  describe "answers_hash" do
    let(:account) { create(:account, tenant: "public") }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, user: user, account: account) }
    let(:evaluation) { create(:evaluation, job: job, user: user, account: account) }
    let(:candidate) { create(:candidate, account: account) }
    let(:apply) { create(:apply, job: job, candidate: candidate, account: account) }
    let(:evaluation_candidate) do
      create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: candidate,
        apply: apply,
        job: job,
        user: user,
        account: account,
        completed: false
      )
    end

    before { Apartment::Tenant.switch!(account.tenant) }
    after { Apartment::Tenant.switch!("public") }

    it "sets a 64-char hex answers_hash when completed becomes true" do
      q = create(:question, evaluation: evaluation, position: 1)
      create(
        :answer,
        question: q,
        evaluation: evaluation,
        candidate: candidate,
        user: user,
        account: account,
        job: job,
        description: "R1"
      )

      evaluation_candidate.update!(completed: true)
      expect(evaluation_candidate.reload.answers_hash).to match(/\A[0-9a-f]{64}\z/)
    end
  end

  describe 'mark_apply_screening_sent callback' do
    let(:account) { create(:account, tenant: "public") }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, user: user, account: account) }
    let(:sp_screening) { create(:selective_process, job: job, account: account, status: :screening) }
    let(:evaluation) { create(:evaluation, job: job, selective_process: sp_screening, user: user, account: account, is_screening: true) }
    let(:candidate) { create(:candidate, account: account) }
    let(:apply) { create(:apply, job: job, candidate: candidate, selective_process: sp_screening, account: account, is_screening_sent: false) }

    before { Apartment::Tenant.switch!(account.tenant) }
    after { Apartment::Tenant.switch!("public") }

    it 'sets is_screening_sent on apply when EvaluationCandidate is created for screening evaluation' do
      expect(apply.is_screening_sent).to be false

      create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, apply: apply, job: job, user: user, account: account)

      expect(apply.reload.is_screening_sent).to be true
    end
  end

  describe "send_internal_evaluation_email callback" do
    let(:account) { create(:account, tenant: "public") }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, user: user, account: account) }
    let(:sp) { create(:selective_process, job: job, account: account, status: :screening) }
    let(:evaluation) do
      create(:evaluation, job: job, selective_process: sp, user: user, account: account,
             is_chatbot: true, chatbot_channel: :internal)
    end
    let(:candidate) { create(:candidate, account: account, email: "candidate@example.com") }

    before { Apartment::Tenant.switch!(account.tenant) }
    after { Apartment::Tenant.switch!("public") }

    it "creates Dispatch with email when EvaluationCandidate is created for internal channel" do
      expect do
        create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, job: job, user: user, account: account)
      end.to change(Dispatch, :count).by(1)

      dispatch = Dispatch.last
      expect(dispatch.channel_type).to eq("email")
      expect(dispatch.subject).to include("convidado")
      expect(dispatch.body).to include("Iniciar Avaliação")
      expect(dispatch.body).to include("/evaluations/")
    end

    it "does not create Dispatch when candidate has no email" do
      candidate.update!(email: nil)

      expect do
        create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, job: job, user: user, account: account)
      end.not_to change(Dispatch, :count)
    end

    it "does not create Dispatch when evaluation is whatsapp channel" do
      evaluation.update!(chatbot_channel: :whatsapp)

      expect do
        create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, job: job, user: user, account: account)
      end.not_to change(Dispatch, :count)
    end
  end
end
