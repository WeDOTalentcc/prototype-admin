# frozen_string_literal: true

require 'rails_helper'

RSpec.describe CandidateFeedback, type: :model do
  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:user) }
    it { should belong_to(:sourcing).optional }
    it { should belong_to(:apply).optional }
    it { should belong_to(:candidate).optional }
    it { should belong_to(:job).optional }
  end

  describe 'validations' do
    it { should validate_presence_of(:feedback_type) }
    it { should validate_presence_of(:user_id) }
    it { should validate_presence_of(:account_id) }

    describe 'feedback_type inclusion' do
      let(:account) { create(:account) }
      let(:user) { create(:user, account: account) }
      let(:candidate) { create(:candidate, account: account) }

      it 'validates inclusion of feedback_type' do
        valid_feedback = described_class.new(
          user: user,
          account: account,
          candidate: candidate,
          feedback_type: 'like'
        )
        expect(valid_feedback).to be_valid

        valid_feedback.feedback_type = 'dislike'
        expect(valid_feedback).to be_valid

        invalid_feedback = described_class.new(
          user: user,
          account: account,
          candidate: candidate,
          feedback_type: 'invalid'
        )
        expect(invalid_feedback).not_to be_valid
        expect(invalid_feedback.errors[:feedback_type]).to be_present
      end
    end

    describe 'at_least_one_context_present validation' do
      let(:account) { create(:account) }
      let(:user) { create(:user, account: account) }

      context 'when all contexts are blank' do
        it 'is invalid' do
          feedback = described_class.new(
            user: user,
            account: account,
            feedback_type: 'like'
          )

          expect(feedback).not_to be_valid
          expect(feedback.errors[:base]).to include("Pelo menos um contexto deve estar presente: sourcing_id, apply_id, candidate_id ou sourced_profile_sourcing_id")
        end
      end

      context 'when sourcing_id is present' do
        let(:sourcing) { create(:sourcing, account: account, user: user) }

        it 'is valid' do
          feedback = described_class.new(
            user: user,
            account: account,
            feedback_type: 'like',
            sourcing: sourcing
          )

          expect(feedback).to be_valid
        end
      end

      context 'when apply_id is present' do
        let(:candidate) { create(:candidate, account: account) }
        let(:job) { create(:job, account: account) }
        let(:selective_process) { create(:selective_process, account: account) }
        let(:apply) { create(:apply, candidate: candidate, job: job, selective_process: selective_process, account: account) }

        it 'is valid' do
          feedback = described_class.new(
            user: user,
            account: account,
            feedback_type: 'like',
            apply: apply
          )

          expect(feedback).to be_valid
        end
      end

      context 'when candidate_id is present' do
        let(:candidate) { create(:candidate, account: account) }

        it 'is valid' do
          feedback = described_class.new(
            user: user,
            account: account,
            feedback_type: 'like',
            candidate: candidate
          )

          expect(feedback).to be_valid
        end
      end

      context 'when sourced_profile_sourcing_id is present' do
        let(:sourcing) { create(:sourcing, account: account, user: user) }
        let(:candidate) { create(:candidate, account: account) }
        let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }
        let(:sourced_profile_sourcing) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user) }

        it 'is valid' do
          feedback = described_class.new(
            user: user,
            account: account,
            feedback_type: 'like',
            sourced_profile_sourcing: sourced_profile_sourcing,
            candidate: candidate
          )

          expect(feedback).to be_valid
        end
      end
    end
  end

  describe 'scopes' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:sourcing) { create(:sourcing, account: account, user: user) }
    let(:candidate1) { create(:candidate, account: account) }
    let(:candidate2) { create(:candidate, account: account) }

    describe '.active' do
      let!(:active_feedback) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate1, is_deleted: false) }
      let!(:deleted_feedback) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate2, is_deleted: true) }

      it 'returns only active feedbacks' do
        expect(described_class.active).to include(active_feedback)
        expect(described_class.active).not_to include(deleted_feedback)
      end
    end

    describe '.likes' do
      let!(:like_feedback) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate1, feedback_type: 'like') }
      let!(:dislike_feedback) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate2, feedback_type: 'dislike') }

      it 'returns only like feedbacks' do
        expect(described_class.likes).to include(like_feedback)
        expect(described_class.likes).not_to include(dislike_feedback)
      end
    end

    describe '.dislikes' do
      let!(:like_feedback) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate1, feedback_type: 'like') }
      let!(:dislike_feedback) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate2, feedback_type: 'dislike') }

      it 'returns only dislike feedbacks' do
        expect(described_class.dislikes).to include(dislike_feedback)
        expect(described_class.dislikes).not_to include(like_feedback)
      end
    end

    describe '.for_sourcing' do
      let(:sourcing2) { create(:sourcing, account: account, user: user) }
      let!(:feedback1) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate1) }
      let!(:feedback2) { create(:candidate_feedback, sourcing: sourcing2, user: user, account: account, candidate: candidate2) }

      it 'returns feedbacks for specific sourcing' do
        expect(described_class.for_sourcing(sourcing.id)).to include(feedback1)
        expect(described_class.for_sourcing(sourcing.id)).not_to include(feedback2)
      end
    end

    describe '.for_sourced_profile_sourcing' do
      let(:sourced_profile1) { create(:sourced_profile, account: account, candidate: candidate1) }
      let(:sourced_profile2) { create(:sourced_profile, account: account, candidate: candidate2) }
      let(:sps1) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile1, sourcing: sourcing, account: account, user: user) }
      let(:sps2) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile2, sourcing: sourcing, account: account, user: user) }
      let!(:feedback1) { create(:candidate_feedback, sourced_profile_sourcing: sps1, user: user, account: account, candidate: candidate1) }
      let!(:feedback2) { create(:candidate_feedback, sourced_profile_sourcing: sps2, user: user, account: account, candidate: candidate2) }

      it 'returns feedbacks for specific sourced_profile_sourcing' do
        expect(described_class.for_sourced_profile_sourcing(sps1.id)).to include(feedback1)
        expect(described_class.for_sourced_profile_sourcing(sps1.id)).not_to include(feedback2)
      end
    end
  end

  describe 'instance methods' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:sourcing) { create(:sourcing, account: account, user: user) }

    describe '#like?' do
      it 'returns true when feedback_type is like' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, feedback_type: 'like')
        expect(feedback.like?).to be true
      end

      it 'returns false when feedback_type is dislike' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, feedback_type: 'dislike')
        expect(feedback.like?).to be false
      end
    end

    describe '#dislike?' do
      it 'returns true when feedback_type is dislike' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, feedback_type: 'dislike')
        expect(feedback.dislike?).to be true
      end

      it 'returns false when feedback_type is like' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, feedback_type: 'like')
        expect(feedback.dislike?).to be false
      end
    end

    describe '#toggle_type!' do
      it 'changes like to dislike' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, feedback_type: 'like')
        expect { feedback.toggle_type! }.to change { feedback.feedback_type }.from('like').to('dislike')
      end

      it 'changes dislike to like' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, feedback_type: 'dislike')
        expect { feedback.toggle_type! }.to change { feedback.feedback_type }.from('dislike').to('like')
      end
    end

    describe '#soft_delete!' do
      it 'marks feedback as deleted' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, is_deleted: false)
        expect { feedback.soft_delete! }.to change { feedback.is_deleted }.from(false).to(true)
      end
    end

    describe '#restore!' do
      it 'restores deleted feedback' do
        candidate = create(:candidate, account: account)
        feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, is_deleted: true)
        expect { feedback.restore! }.to change { feedback.is_deleted }.from(true).to(false)
      end
    end
  end

  describe 'class methods' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:sourcing) { create(:sourcing, account: account, user: user) }
    let(:candidate) { create(:candidate, account: account) }

    describe '.find_existing' do
      context 'with sourcing and candidate' do
        let!(:feedback) { create(:candidate_feedback, sourcing: sourcing, candidate: candidate, user: user, account: account) }

        it 'finds existing feedback' do
          result = described_class.find_existing(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user_id: user.id
          )
          expect(result).to eq(feedback)
        end

        it 'returns nil when not found' do
          result = described_class.find_existing(
            sourcing_id: 999,
            candidate_id: candidate.id,
            user_id: user.id
          )
          expect(result).to be_nil
        end
      end

      context 'with apply' do
        let(:job) { create(:job, account: account) }
        let(:selective_process) { create(:selective_process, account: account) }
        let(:apply) { create(:apply, candidate: candidate, job: job, selective_process: selective_process, account: account) }
        let!(:feedback) { create(:candidate_feedback, apply: apply, user: user, account: account) }

        it 'finds existing feedback by apply_id' do
          result = described_class.find_existing(
            apply_id: apply.id,
            user_id: user.id
          )
          expect(result).to eq(feedback)
        end
      end

      context 'with sourced_profile_sourcing' do
        let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }
        let(:sourced_profile_sourcing) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user) }
        let!(:feedback) { create(:candidate_feedback, sourced_profile_sourcing: sourced_profile_sourcing, user: user, account: account, candidate: candidate) }

        it 'finds existing feedback by sourced_profile_sourcing_id' do
          result = described_class.find_existing(
            sourced_profile_sourcing_id: sourced_profile_sourcing.id,
            user_id: user.id
          )
          expect(result).to eq(feedback)
        end
      end
    end

    describe '.stats_for_sourcing' do
      let!(:like_feedback1) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate, feedback_type: 'like') }
      let!(:like_feedback2) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: create(:candidate, account: account), feedback_type: 'like') }
      let!(:dislike_feedback) { create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: create(:candidate, account: account), feedback_type: 'dislike') }

      it 'returns feedback counts by type' do
        stats = described_class.stats_for_sourcing(sourcing.id)
        expect(stats['like']).to eq(2)
        expect(stats['dislike']).to eq(1)
      end
    end

    describe '.stats_for_candidate' do
      let(:sourcing2) { create(:sourcing, account: account, user: user) }
      let!(:like_feedback) { create(:candidate_feedback, sourcing: sourcing, candidate: candidate, user: user, account: account, feedback_type: 'like') }
      let!(:dislike_feedback) { create(:candidate_feedback, sourcing: sourcing2, candidate: candidate, user: user, account: account, feedback_type: 'dislike') }

      it 'returns feedback counts by type for a candidate' do
        stats = described_class.stats_for_candidate(candidate.id)
        expect(stats['like']).to eq(1)
        expect(stats['dislike']).to eq(1)
      end
    end

    describe '.stats_for_sourced_profile_sourcing' do
      let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }
      let(:sourced_profile_sourcing) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user) }
      let!(:like_feedback1) { create(:candidate_feedback, sourced_profile_sourcing: sourced_profile_sourcing, user: user, account: account, candidate: candidate, feedback_type: 'like') }
      let!(:like_feedback2) { create(:candidate_feedback, sourced_profile_sourcing: sourced_profile_sourcing, user: create(:user, account: account), account: account, candidate: candidate, feedback_type: 'like') }
      let!(:dislike_feedback) { create(:candidate_feedback, sourced_profile_sourcing: sourced_profile_sourcing, user: create(:user, account: account), account: account, candidate: candidate, feedback_type: 'dislike') }

      it 'returns feedback counts by type for a sourced_profile_sourcing' do
        stats = described_class.stats_for_sourced_profile_sourcing(sourced_profile_sourcing.id)
        expect(stats['like']).to eq(2)
        expect(stats['dislike']).to eq(1)
      end
    end
  end
end
