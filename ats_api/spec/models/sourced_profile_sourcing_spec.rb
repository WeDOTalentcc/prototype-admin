# frozen_string_literal: true

require 'rails_helper'

RSpec.describe SourcedProfileSourcing, type: :model do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:sourcing) { create(:sourcing, account: account, user: user) }
  let(:candidate) { create(:candidate, account: account) }
  let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }
  let(:sourced_profile_sourcing) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user) }

  describe "associations" do
    it { is_expected.to belong_to(:sourced_profile) }
    it { is_expected.to belong_to(:sourcing) }
    it { is_expected.to belong_to(:account) }
    it { is_expected.to belong_to(:user) }
  end

  describe "validations" do
    it { is_expected.to validate_presence_of(:sourced_profile_id) }
    it { is_expected.to validate_presence_of(:sourcing_id) }
    it { is_expected.to validate_presence_of(:account_id) }
    it { is_expected.to validate_presence_of(:user_id) }

    describe "uniqueness" do
      subject { sourced_profile_sourcing }

      it { is_expected.to validate_uniqueness_of(:sourced_profile_id).scoped_to(:sourcing_id) }
    end
  end

  describe '#get_candidate_feedback_type' do
    context 'when there is no feedback' do
      it 'returns nil' do
        expect(sourced_profile_sourcing.get_candidate_feedback_type).to be_nil
      end
    end

    context 'when there is a like feedback' do
      before do
        create(:candidate_feedback,
          sourced_profile_sourcing: sourced_profile_sourcing,
          user: user,
          account: account,
          candidate: candidate,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      it 'returns "like"' do
        expect(sourced_profile_sourcing.get_candidate_feedback_type).to eq('like')
      end
    end

    context 'when there is a dislike feedback' do
      before do
        create(:candidate_feedback,
          sourced_profile_sourcing: sourced_profile_sourcing,
          user: user,
          account: account,
          candidate: candidate,
          feedback_type: 'dislike',
          is_deleted: false
        )
      end

      it 'returns "dislike"' do
        expect(sourced_profile_sourcing.get_candidate_feedback_type).to eq('dislike')
      end
    end

    context 'when feedback is deleted' do
      before do
        create(:candidate_feedback,
          sourced_profile_sourcing: sourced_profile_sourcing,
          user: user,
          account: account,
          candidate: candidate,
          feedback_type: 'like',
          is_deleted: true
        )
      end

      it 'returns nil' do
        expect(sourced_profile_sourcing.get_candidate_feedback_type).to be_nil
      end
    end

    context 'when feedback exists with sourcing_id + candidate_id (fallback/legacy)' do
      before do
        create(:candidate_feedback,
          sourcing: sourcing,
          candidate: candidate,
          user: user,
          account: account,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      it 'returns "like" via fallback' do
        expect(sourced_profile_sourcing.get_candidate_feedback_type).to eq('like')
      end
    end

    context 'when both direct and fallback feedbacks exist' do
      before do
        create(:candidate_feedback,
          sourcing: sourcing,
          candidate: candidate,
          user: user,
          account: account,
          feedback_type: 'dislike',
          is_deleted: false
        )

        create(:candidate_feedback,
          sourced_profile_sourcing: sourced_profile_sourcing,
          user: user,
          account: account,
          candidate: candidate,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      it 'returns feedback from direct association (priority)' do
        expect(sourced_profile_sourcing.get_candidate_feedback_type).to eq('like')
      end
    end
  end

  describe '#search_data' do
    it 'includes candidate_feedback field' do
      search_data = sourced_profile_sourcing.search_data
      expect(search_data).to have_key(:candidate_feedback)
    end

    context 'with like feedback' do
      before do
        create(:candidate_feedback,
          sourced_profile_sourcing: sourced_profile_sourcing,
          user: user,
          account: account,
          candidate: candidate,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      it 'includes the feedback type in search_data' do
        search_data = sourced_profile_sourcing.search_data
        expect(search_data[:candidate_feedback]).to eq('like')
      end
    end
  end
end
