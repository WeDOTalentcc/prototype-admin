require 'rails_helper'

RSpec.describe Occupation, type: :model do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:user).optional }
  end

  describe 'validations' do
    subject { create(:occupation, name: "Developer", account: account, user: user) }

    it { should validate_presence_of(:name) }

    it 'validates uniqueness of name scoped to account and not soft-deleted' do
      create(:occupation, name: "Designer", account: account, is_deleted: false)
      duplicate = build(:occupation, name: "Designer", account: account, is_deleted: false)
      expect(duplicate).not_to be_valid
      expect(duplicate.errors[:name]).to include("Ocupação já existe")
    end

    it 'allows same name if previous is soft deleted' do
      create(:occupation, name: "Manager", account: account, is_deleted: true)
      new_occupation = build(:occupation, name: "Manager", account: account, is_deleted: false)
      expect(new_occupation).to be_valid
    end

    it 'allows same name in different accounts' do
      other_account = create(:account)
      create(:occupation, name: "DevOps", account: other_account)
      occupation = build(:occupation, name: "DevOps", account: account)
      expect(occupation).to be_valid
    end
  end
end
