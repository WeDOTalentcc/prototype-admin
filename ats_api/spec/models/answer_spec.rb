require 'rails_helper'

RSpec.describe Answer, type: :model do
  subject { build(:answer) }

  it { should belong_to(:question).optional }
  it { should belong_to(:evaluation).optional }
  it { should belong_to(:candidate).optional }
  it { should belong_to(:job).optional }
  it { should belong_to(:apply).optional }
  it { should belong_to(:user).optional }
  it { should belong_to(:account).optional }
  it { should belong_to(:reference).optional }

  it 'is valid with factory defaults' do
    expect(subject).to be_valid
  end

  context 'with associations' do
    it 'can be linked to question and evaluation' do
      answer = build(:answer, :with_question, :with_evaluation)
      expect(answer.question).to be_present
      expect(answer.evaluation).to be_present
      expect(answer).to be_valid
    end
  end

  describe "wsi fields" do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }

    it "clears self_declaration_score for behavioral questions" do
      q = create(:question, evaluation: evaluation, competence_type: "behavioral")
      answer = build(
        :answer,
        question: q,
        evaluation: evaluation,
        user: user,
        account: account,
        job: job,
        self_declaration_score: 4
      )
      answer.valid?
      expect(answer.self_declaration_score).to be_nil
    end

    it "clears eligibility_answer for technical questions" do
      q = create(:question, evaluation: evaluation, competence_type: "technical")
      answer = build(
        :answer,
        question: q,
        evaluation: evaluation,
        user: user,
        account: account,
        job: job,
        eligibility_answer: false
      )
      answer.valid?
      expect(answer.eligibility_answer).to be_nil
    end
  end
end
