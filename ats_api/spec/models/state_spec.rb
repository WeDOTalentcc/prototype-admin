require 'rails_helper'

RSpec.describe State, type: :model do
  let(:country) { create(:country) }

  describe 'associations' do
    it { should belong_to(:country) }
  end

  describe 'validations' do
    it { should validate_presence_of(:name) }

    it 'validates uniqueness of name scoped to country' do
      create(:state, name: 'São Paulo', country: country)
      expect(build(:state, name: 'São Paulo', country: country)).not_to be_valid
    end

    it 'allows same name in different countries' do
      other_country = create(:country, name: 'Argentina')
      create(:state, name: 'São Paulo', country: country)
      expect(build(:state, name: 'São Paulo', country: other_country)).to be_valid
    end
  end

  describe 'search functionality' do
    it 'includes Searchable module' do
      expect(State.included_modules).to include(Searchable)
    end
  end
end
