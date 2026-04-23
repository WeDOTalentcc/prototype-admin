require 'rails_helper'

RSpec.describe SkillCategory, type: :model do
  subject { build(:skill_category) }

  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_uniqueness_of(:name) }
  end

  describe 'associations' do
    it { should have_many(:skills).dependent(:nullify) }
  end

  describe 'searchable' do
    it 'includes Searchable concern' do
      expect(SkillCategory.included_modules).to include(Searchable)
    end
  end

  describe '#search_data' do
    let(:skill_category) { create(:skill_category, :programming) }
    let!(:skill1) { create(:skill, skill_category: skill_category) }
    let!(:skill2) { create(:skill, skill_category: skill_category) }

    it 'returns correct search data structure' do
      search_data = skill_category.search_data

      expect(search_data).to include(
        id: skill_category.id,
        name: skill_category.name,
        description: skill_category.description,
        icon: skill_category.icon,
        color: skill_category.color,
        is_deleted: false
      )
    end

    it 'includes skills count' do
      search_data = skill_category.search_data
      expect(search_data[:skills_count]).to eq(2)
    end

    it 'excludes deleted skills from count' do
      skill1.update(is_deleted: true)
      search_data = skill_category.search_data
      expect(search_data[:skills_count]).to eq(1)
    end
  end

  describe 'soft delete' do
    let(:skill_category) { create(:skill_category) }
    let!(:skill) { create(:skill, skill_category: skill_category) }

    it 'does not delete skills when category is soft deleted' do
      skill_category.update(is_deleted: true)
      expect(skill.reload.skill_category_id).to eq(skill_category.id)
    end
  end

  describe 'factory' do
    it 'has a valid factory' do
      expect(build(:skill_category)).to be_valid
    end

    it 'has valid traits' do
      expect(build(:skill_category, :programming)).to be_valid
      expect(build(:skill_category, :backend)).to be_valid
      expect(build(:skill_category, :soft_skills)).to be_valid
      expect(build(:skill_category, :deleted)).to be_valid
    end
  end
end
