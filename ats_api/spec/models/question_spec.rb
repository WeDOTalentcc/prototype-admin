# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Question, type: :model do
  subject { build(:question) }

  describe 'associations' do
    it { should belong_to(:evaluation) }
    it { should belong_to(:selective_process).optional }
    it { should belong_to(:parent_question).class_name('Question').optional }
    it { should have_many(:sub_questions).class_name('Question').with_foreign_key('parent_question_id').dependent(:nullify) }
  end

  describe 'validations' do
    it { should validate_presence_of(:title) }
    it { should validate_presence_of(:response_type) }
  end

  it 'has a valid factory' do
    expect(subject).to be_valid
  end

  describe "questions_hash on evaluation" do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }

    it "refreshes evaluation.questions_hash after create" do
      create(:question, evaluation: evaluation, position: 1)
      evaluation.reload
      expect(evaluation.questions_hash).to match(/\A[0-9a-f]{64}\z/)
    end

    it "refreshes evaluation.questions_hash after update" do
      q = create(:question, evaluation: evaluation, position: 1, title: "One")
      evaluation.reload
      first_hash = evaluation.questions_hash
      q.update!(title: "Two")
      evaluation.reload
      expect(evaluation.questions_hash).to match(/\A[0-9a-f]{64}\z/)
      expect(evaluation.questions_hash).not_to eq(first_hash)
    end

    it "refreshes evaluation.questions_hash after destroy" do
      q = create(:question, evaluation: evaluation, position: 1)
      evaluation.reload
      with_q = evaluation.questions_hash
      q.destroy!
      evaluation.reload
      expect(evaluation.questions_hash).not_to eq(with_q)
      expect(evaluation.questions_hash).to eq(Digest::SHA256.hexdigest(JSON.generate([])))
    end
  end

  describe "wsi_metadata" do
    it "persists nested keys used by WSI generation" do
      q = create(
        :question,
        wsi_metadata: {
          "reviewed_by_recruiter" => false,
          "needs_manual_review" => true,
          "generation_attempts" => 3,
          "skill_name" => "Ruby",
          "trait_weight" => 0.2,
          "_skill_approximated" => true
        }
      )

      q.reload
      expect(q.wsi_metadata["needs_manual_review"]).to be true
      expect(q.wsi_metadata["generation_attempts"]).to eq(3)
      expect(q.wsi_metadata["_skill_approximated"]).to be true
    end
  end
end
