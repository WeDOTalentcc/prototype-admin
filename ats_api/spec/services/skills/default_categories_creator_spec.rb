require 'rails_helper'

RSpec.describe Skills::DefaultCategoriesCreator do
  let(:account) { create(:account) }

  describe '.create_for_account' do
    it 'creates default skill categories' do
      expect {
        described_class.create_for_account(account)
      }.to change(SkillCategory, :count).by(40)
    end

    it 'creates categories with correct attributes' do
      described_class.create_for_account(account)

      programming_category = SkillCategory.find_by(name: 'Linguagens de Programação')
      expect(programming_category).to be_present
      expect(programming_category.description).to eq('Linguagens de programação e scripting')
      expect(programming_category.icon).to eq('💻')
      expect(programming_category.color).to eq('#3B82F6')
      expect(programming_category.is_deleted).to be_falsey
    end

    it 'skips existing categories' do
      create(:skill_category, name: 'Linguagens de Programação')

      expect {
        described_class.create_for_account(account)
      }.to change(SkillCategory, :count).by(39)
    end

    it 'returns correct statistics' do
      result = described_class.create_for_account(account)

      expect(result[:created]).to eq(40)
      expect(result[:skipped]).to eq(0)
      expect(result[:total]).to eq(40)
    end

    it 'returns correct statistics with existing categories' do
      create(:skill_category, name: 'Linguagens de Programação')
      create(:skill_category, name: 'Soft Skills')

      result = described_class.create_for_account(account)

      expect(result[:created]).to eq(38)
      expect(result[:skipped]).to eq(2)
      expect(result[:total]).to eq(40)
    end

    it 'handles validation errors gracefully' do
      allow_any_instance_of(SkillCategory).to receive(:save).and_return(false)
      allow_any_instance_of(SkillCategory).to receive(:errors).and_return(
        double(full_messages: [ 'Name has already been taken' ])
      )

      result = described_class.create_for_account(account)
      expect(result[:created]).to eq(0)
    end
  end

  describe 'category completeness' do
    let(:test_account) { create(:account) }

    before do
      described_class.create_for_account(test_account)
    end

    it 'creates exactly 40 categories' do
      expect(SkillCategory.count).to eq(40)
    end

    it 'all categories have required fields' do
      SkillCategory.limit(5).each do |category|
        expect(category.name).to be_present
        expect(category.description).to be_present
        expect(category.icon).to be_present
        expect(category.color).to be_present
        expect(category.color).to match(/^#[0-9A-F]{6}$/i)
      end
    end

    it 'all categories have unique names' do
      names = SkillCategory.pluck(:name)
      expect(names.uniq.count).to eq(names.count)
    end

    it 'all categories have valid hex colors' do
      colors = SkillCategory.pluck(:color)
      colors.each do |color|
        expect(color).to match(/^#[0-9A-F]{6}$/i)
      end
    end

    it 'includes key tech categories' do
      tech_names = [ 'Linguagens de Programação', 'Frameworks Backend', 'DevOps & Cloud' ]
      tech_names.each do |name|
        expect(SkillCategory.exists?(name: name)).to be_truthy
      end
    end

    it 'includes key business categories' do
      business_names = [ 'Marketing Digital', 'Vendas & CRM', 'Recursos Humanos' ]
      business_names.each do |name|
        expect(SkillCategory.exists?(name: name)).to be_truthy
      end
    end
  end
end
