# frozen_string_literal: true

require 'rails_helper'

RSpec.describe CandidateFeedbacks::UpsertService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:sourcing) { create(:sourcing, account: account, user: user) }
  let(:candidate) { create(:candidate, account: account) }
  let(:job) { create(:job, account: account, user: user) }

  describe '#call' do
    describe 'validations' do
      context 'when user is blank' do
        it 'returns error' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: nil,
            feedback_type: 'like'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("User is required")
        end
      end

      context 'when all contexts are blank' do
        it 'returns error' do
          result = described_class.call(
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("At least one context must be present")
        end
      end

      context 'when feedback_type is invalid' do
        it 'returns error' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'invalid'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("Invalid feedback type")
        end
      end

      context 'when sourcing does not exist' do
        it 'returns error' do
          result = described_class.call(
            sourcing_id: 99999,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("Sourcing not found")
        end
      end

      context 'when candidate does not exist' do
        it 'returns error' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: 99999,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("Candidate not found")
        end
      end
    end

    describe 'creating new feedback' do
      context 'when no feedback exists' do
        it 'creates a new feedback' do
          expect {
            described_class.call(
              sourcing_id: sourcing.id,
              candidate_id: candidate.id,
              user: user,
              feedback_type: 'like',
              job_id: job.id
            )
          }.to change(CandidateFeedback, :count).by(1)
        end

        it 'returns success with action :created' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'like',
            job_id: job.id
          )

          expect(result[:success]).to be true
          expect(result[:action]).to eq(:created)
          expect(result[:feedback]).to be_a(CandidateFeedback)
          expect(result[:feedback].feedback_type).to eq('like')
        end

        it 'assigns correct attributes' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'like',
            job_id: job.id
          )

          feedback = result[:feedback]
          expect(feedback.sourcing_id).to eq(sourcing.id)
          expect(feedback.candidate_id).to eq(candidate.id)
          expect(feedback.user_id).to eq(user.id)
          expect(feedback.account_id).to eq(account.id)
          expect(feedback.job_id).to eq(job.id)
          expect(feedback.feedback_type).to eq('like')
          expect(feedback.is_deleted).to be false
        end

        it 'saves search_query_snapshot' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'like'
          )

          feedback = result[:feedback]
          expect(feedback.search_query_snapshot).to be_present
          expect(feedback.search_query_snapshot['query']).to eq(sourcing.query)
        end
      end
    end

    describe 'toggle logic - same type' do
      context 'when feedback exists with same type' do
        let!(:existing_feedback) do
          create(:candidate_feedback,
            sourcing: sourcing,
            candidate: candidate,
            user: user,
            account: account,
            feedback_type: 'like',
            is_deleted: false
          )
        end

        it 'does not create new feedback' do
          expect {
            described_class.call(
              sourcing_id: sourcing.id,
              candidate_id: candidate.id,
              user: user,
              feedback_type: 'like'
            )
          }.not_to change(CandidateFeedback, :count)
        end

        it 'soft deletes the existing feedback' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be true
          expect(result[:action]).to eq(:removed)
          expect(result[:feedback].is_deleted).to be true
        end
      end
    end

    describe 'toggle logic - different type' do
      context 'when feedback exists with different type' do
        let!(:existing_feedback) do
          create(:candidate_feedback,
            sourcing: sourcing,
            candidate: candidate,
            user: user,
            account: account,
            feedback_type: 'like',
            is_deleted: false
          )
        end

        it 'does not create new feedback' do
          expect {
            described_class.call(
              sourcing_id: sourcing.id,
              candidate_id: candidate.id,
              user: user,
              feedback_type: 'dislike'
            )
          }.not_to change(CandidateFeedback, :count)
        end

        it 'updates the feedback type' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'dislike'
          )

          expect(result[:success]).to be true
          expect(result[:action]).to eq(:updated)

          existing_feedback.reload
          expect(existing_feedback.feedback_type).to eq('dislike')
          expect(existing_feedback.is_deleted).to be false
        end

        it 'updates snapshots' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'dislike'
          )

          existing_feedback.reload
          expect(existing_feedback.search_query_snapshot).to be_present
        end
      end
    end

    describe 'multi-tenant scoping' do
      let(:other_account) { create(:account) }
      let(:other_user) { create(:user, account: other_account) }
      let(:other_sourcing) { create(:sourcing, account: other_account, user: other_user) }
      let(:other_candidate) { create(:candidate, account: other_account) }

      context 'when sourcing belongs to different account' do
        it 'returns error' do
          result = described_class.call(
            sourcing_id: other_sourcing.id,
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("Sourcing not found")
        end
      end

      context 'when candidate belongs to different account' do
        it 'returns error' do
          result = described_class.call(
            sourcing_id: sourcing.id,
            candidate_id: other_candidate.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("Candidate not found")
        end
      end

      it 'always assigns feedback to user account' do
        result = described_class.call(
          sourcing_id: sourcing.id,
          candidate_id: candidate.id,
          user: user,
          feedback_type: 'like'
        )

        expect(result[:feedback].account_id).to eq(user.account_id)
      end
    end

    describe 'multiple contexts' do
      context 'with apply_id context' do
        let(:selective_process) { create(:selective_process, account: account) }
        let(:apply) { create(:apply, candidate: candidate, job: job, selective_process: selective_process, account: account) }

        it 'creates feedback with apply context' do
          result = described_class.call(
            apply_id: apply.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be true
          expect(result[:feedback].apply_id).to eq(apply.id)
          expect(result[:feedback].candidate_id).to eq(candidate.id)
          expect(result[:feedback].job_id).to eq(job.id)
        end
      end

      context 'with only candidate_id context' do
        it 'creates feedback with only candidate' do
          result = described_class.call(
            candidate_id: candidate.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be true
          expect(result[:feedback].candidate_id).to eq(candidate.id)
          expect(result[:feedback].sourcing_id).to be_nil
          expect(result[:feedback].apply_id).to be_nil
        end
      end
    end

    describe 'snapshots' do
      it 'saves search_query_snapshot with sourcing data' do
        result = described_class.call(
          sourcing_id: sourcing.id,
          candidate_id: candidate.id,
          user: user,
          feedback_type: 'like'
        )

        snapshot = result[:feedback].search_query_snapshot
        expect(snapshot).to be_a(Hash)
        expect(snapshot['query']).to eq(sourcing.query)
        expect(snapshot['provider']).to eq(sourcing.provider)
        expect(snapshot['searched_at']).to be_present
      end

      it 'saves empty snapshot when no sourcing' do
        result = described_class.call(
          candidate_id: candidate.id,
          user: user,
          feedback_type: 'like'
        )

        expect(result[:feedback].search_query_snapshot).to eq({})
      end
    end

    describe 'sourced_profile_sourcing context' do
      let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }
      let(:sourced_profile_sourcing) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user) }

      context 'when creating feedback with sourced_profile_sourcing_id' do
        it 'creates feedback successfully' do
          result = described_class.call(
            sourced_profile_sourcing_id: sourced_profile_sourcing.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be true
          expect(result[:action]).to eq(:created)
          expect(result[:feedback].sourced_profile_sourcing_id).to eq(sourced_profile_sourcing.id)
          expect(result[:feedback].sourcing_id).to eq(sourcing.id)
          expect(result[:feedback].candidate_id).to eq(candidate.id)
        end

        it 'saves candidate_score_snapshot from sourced_profile_sourcing' do
          result = described_class.call(
            sourced_profile_sourcing_id: sourced_profile_sourcing.id,
            user: user,
            feedback_type: 'like'
          )

          snapshot = result[:feedback].candidate_score_snapshot
          expect(snapshot).to be_a(Hash)
          expect(snapshot['sourcing_score']).to eq(sourced_profile_sourcing.score)
          expect(snapshot['search_source']).to eq(sourced_profile_sourcing.search_source)
          expect(snapshot['search_score'].to_f).to eq(sourced_profile_sourcing.search_score.to_f)
        end
      end

      context 'when sourced_profile_sourcing does not exist' do
        it 'returns error' do
          result = described_class.call(
            sourced_profile_sourcing_id: 99999,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be false
          expect(result[:errors]).to include("SourcedProfileSourcing not found")
        end
      end

      context 'when toggling feedback' do
        before do
          described_class.call(
            sourced_profile_sourcing_id: sourced_profile_sourcing.id,
            user: user,
            feedback_type: 'like'
          )
        end

        it 'removes feedback when same type' do
          result = described_class.call(
            sourced_profile_sourcing_id: sourced_profile_sourcing.id,
            user: user,
            feedback_type: 'like'
          )

          expect(result[:success]).to be true
          expect(result[:action]).to eq(:removed)
          expect(result[:feedback].is_deleted).to be true
        end

        it 'updates feedback when different type' do
          result = described_class.call(
            sourced_profile_sourcing_id: sourced_profile_sourcing.id,
            user: user,
            feedback_type: 'dislike'
          )

          expect(result[:success]).to be true
          expect(result[:action]).to eq(:updated)
          expect(result[:feedback].feedback_type).to eq('dislike')
        end
      end
    end
  end
end
