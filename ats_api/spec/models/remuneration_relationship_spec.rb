require 'rails_helper'

RSpec.describe RemunerationRelationship, type: :model do
  describe 'associations' do
    it { should belong_to(:remuneration) }
    it { should belong_to(:account) }
    it { should belong_to(:user).optional }
  end

  describe 'validations' do
    subject {
      create(:remuneration_relationship)
    }

    it { should validate_presence_of(:remuneration) }
    it { should validate_presence_of(:reference_type) }
    it { should validate_presence_of(:reference_id) }

    it {
      should validate_uniqueness_of(:reference_id)
        .scoped_to(:reference_type, :remuneration_id)
        .with_message("Remuneration already linked to this reference")
    }
  end

  describe 'factory' do
    it 'is valid with valid attributes' do
      rr = build(:remuneration_relationship)
      expect(rr).to be_valid
    end
  end
end
