require 'rails_helper'

RSpec.describe Skill, type: :model do
  let(:account) { create(:account) }
  subject { build(:skill, account: account) }

  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_presence_of(:account_id) }

    it 'validates uniqueness of name scoped to account_id' do
      create(:skill, name: 'Ruby', account: account)
      duplicate = build(:skill, name: 'Ruby', account: account)
      expect(duplicate).not_to be_valid
      expect(duplicate.errors[:name]).to include('Skill name must be unique for the account')
    end

    it 'allows same name for different accounts' do
      account1 = create(:account)
      account2 = create(:account)
      create(:skill, name: 'Ruby', account: account1)
      duplicate = build(:skill, name: 'Ruby', account: account2)
      expect(duplicate).to be_valid
    end
  end

  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:skill_category).optional }
  end

  describe 'searchable' do
    it 'includes Searchable concern' do
      expect(Skill.included_modules).to include(Searchable)
    end
  end

  describe '#search_data' do
    context 'with skill_category' do
      let(:category) { create(:skill_category, :programming) }
      let(:skill) { create(:skill, skill_category: category) }

      it 'returns correct search data with category information' do
        search_data = skill.search_data

        expect(search_data).to include(
          id: skill.id,
          name: skill.name,
          is_deleted: false,
          account_id: skill.account_id,
          skill_category_id: category.id,
          skill_category_name: category.name
        )
      end
    end

    context 'without skill_category' do
      let(:skill) { create(:skill) }

      it 'returns search data with nil category fields' do
        search_data = skill.search_data

        expect(search_data).to include(
          skill_category_id: nil,
          skill_category_name: nil
        )
      end
    end
  end

  describe 'optional skill_category' do
    it 'is valid without skill_category' do
      skill = build(:skill, account: account, skill_category: nil)
      expect(skill).to be_valid
    end

    it 'is valid with skill_category' do
      skill = build(:skill, :with_category, account: account)
      expect(skill).to be_valid
    end
  end

  describe 'factory' do
    it 'has a valid factory' do
      expect(build(:skill, account: account)).to be_valid
    end

    it 'has valid traits' do
      expect(build(:skill, :with_category, account: account)).to be_valid
      expect(build(:skill, :programming_language, account: account)).to be_valid
      expect(build(:skill, :backend_framework, account: account)).to be_valid
      expect(build(:skill, :soft_skill, account: account)).to be_valid
      expect(build(:skill, :deleted, account: account)).to be_valid
    end
  end
end
