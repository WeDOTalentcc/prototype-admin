require 'rails_helper'

RSpec.describe AddressRelationship, type: :model do
  describe 'modules' do
    it 'includes Searchable module' do
      expect(described_class.included_modules).to include(Searchable)
    end
  end

  describe 'associations' do
    it { is_expected.to belong_to(:address) }
    it { is_expected.to belong_to(:account) }
    it { is_expected.to belong_to(:user).optional }
  end

  describe 'validations' do
    subject { create(:address_relationship) } # Necessário para testar unicidade

    it { is_expected.to validate_presence_of(:reference_type) }
    it { is_expected.to validate_presence_of(:reference_id) }
    it { is_expected.to validate_presence_of(:address) }

    # Testa unicidade básica
    it do
      expect(subject).to validate_uniqueness_of(:reference_id)
        .scoped_to(:reference_type, :address_id)
        .with_message('Reference must be unique for the addresss')
    end
  end

  describe 'uniqueness with soft delete' do
    let(:account) { create(:account) }
    let(:address) { create(:address, account: account) }

    it 'allows duplicate when one is soft deleted' do
      create(:address_relationship, reference_id: 1, reference_type: 'Test', address: address, account: account, is_deleted: true)
      rel = build(:address_relationship, reference_id: 1, reference_type: 'Test', address: address, account: account, is_deleted: false)
      expect(rel).to be_valid
    end

    it 'does not allow duplicate when both are active' do
      create(:address_relationship, reference_id: 1, reference_type: 'Test', address: address, account: account, is_deleted: false)
      rel = build(:address_relationship, reference_id: 1, reference_type: 'Test', address: address, account: account, is_deleted: false)
      expect(rel).not_to be_valid
      expect(rel.errors[:reference_id]).to include('Reference must be unique for the addresss')
    end
  end
end
