require 'rails_helper'

RSpec.describe Remuneration, type: :model do
  describe 'associations' do
    it { should belong_to(:account).optional(false) }
    it { should belong_to(:user).optional }
  end

  describe 'validations' do
    subject { build(:remuneration) }

    it { should validate_presence_of(:name) }

    it 'validates uniqueness of name scoped to account and description' do
      account = create(:account)
      Remuneration.create!(
        name: 'Base Salary',
        account: account,
        description: 'Full time'
      )

      duplicate = Remuneration.new(
        name: 'Base Salary',
        account: account,
        description: 'Full time'
      )

      expect(duplicate).not_to be_valid
      expect(duplicate.errors[:name]).to include('Remuneration name must be unique for the account')
    end

    it 'allows same name for different accounts or descriptions' do
      account1 = create(:account)
      account2 = create(:account)

      create(:remuneration, name: 'Bonus', account: account1, description: 'Annual')

      expect(build(:remuneration, name: 'Bonus', account: account2, description: 'Annual')).to be_valid
      expect(build(:remuneration, name: 'Bonus', account: account1, description: 'Monthly')).to be_valid
    end
  end
end
