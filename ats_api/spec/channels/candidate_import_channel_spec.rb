require 'rails_helper'

RSpec.describe CandidateImportChannel, type: :channel do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  before do
    stub_connection current_user: user
  end

  describe '#subscribed' do
    context 'with valid user_id' do
      it 'subscribes to the user account stream' do
        subscribe(user_id: user.id)

        expect(subscription).to be_confirmed
        expect(subscription).to have_stream_from("candidate_import_#{account.id}")
      end
    end

    context 'with invalid user_id' do
      it 'does not subscribe' do
        subscribe(user_id: 999999)

        expect(subscription).to be_confirmed
        expect(subscription).not_to have_stream_from("candidate_import_#{account.id}")
      end
    end

    context 'without user_id' do
      it 'does not subscribe' do
        subscribe

        expect(subscription).to be_confirmed
        expect(subscription).not_to have_stream_from("candidate_import_#{account.id}")
      end
    end
  end

  describe '#unsubscribed' do
    it 'stops all streams' do
      subscribe(user_id: user.id)
      expect(subscription).to have_stream_from("candidate_import_#{account.id}")

      unsubscribe
      expect(subscription).not_to have_streams
    end
  end
end
