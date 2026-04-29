require 'rails_helper'

RSpec.describe Address, type: :model do
  describe 'modules' do
    it 'includes Searchable module' do
      expect(described_class.included_modules).to include(Searchable)
    end
  end

  describe 'associations' do
    it { is_expected.to belong_to(:city).optional }
    it { is_expected.to belong_to(:state).optional }
    it { is_expected.to belong_to(:country).optional }
    it { is_expected.to belong_to(:user).optional }
    it { is_expected.to belong_to(:account) }
  end

  describe 'database columns' do
    it { is_expected.to have_db_column(:city_id).of_type(:integer) }
    it { is_expected.to have_db_column(:state_id).of_type(:integer) }
    it { is_expected.to have_db_column(:country_id).of_type(:integer) }
    it { is_expected.to have_db_column(:user_id).of_type(:integer) }
    it { is_expected.to have_db_column(:account_id).of_type(:integer) }
  end

  describe 'validations' do
    it 'is valid with only account' do
      account = create(:account)
      address = build(:address, account: account)
      expect(address).to be_valid
    end

    it 'is invalid without account' do
      address = build(:address, account: nil)
      expect(address).not_to be_valid
      expect(address.errors[:account]).to include("must exist")
    end
  end
end
