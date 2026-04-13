# spec/models/apply_spec.rb
require 'rails_helper'

RSpec.describe Apply, type: :model do
  describe 'associations' do
    it { should belong_to(:candidate) }
    it { should belong_to(:job) }
    it { should belong_to(:selective_process) }
  end

  describe 'defaults' do
    it 'sets is_deleted to false by default' do
      apply = described_class.new
      expect(apply.is_deleted).to eq(false)
    end
  end

   describe 'callbacks' do
    let(:user) { create(:user) }
    let(:account) { user.account }
    let(:candidate) { create(:candidate, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:selective_process_1) { create(:selective_process, account: account) }
    let(:selective_process_2) { create(:selective_process, account: account) }

    before do
      Current.user = user
    end

    it 'creates an ApplyStatus when selective_process_id changes' do
      apply = create(
        :apply,
        candidate: candidate,
        job: job,
        selective_process: selective_process_1,
        account_id: account.id
      )

      expect {
        apply.update!(selective_process: selective_process_2)
      }.to change(ApplyStatus, :count).by(1)

      status = ApplyStatus.last
      expect(status.apply).to eq(apply)
      expect(status.selective_process).to eq(selective_process_2)
      expect(status.user_id).to eq(user.id)
      expect(status.account_id).to eq(account.id)
    end
  end
end
