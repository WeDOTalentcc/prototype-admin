# frozen_string_literal: true

require 'rails_helper'

RSpec.describe EmailTemplate, type: :model do
  subject { build(:email_template) }

  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:user) }
  end

  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_presence_of(:subject) }
    it { should validate_presence_of(:content) }
    it { should validate_presence_of(:category_id) }
  end

  describe 'factory' do
    it 'has a valid factory' do
      expect(subject).to be_valid
    end

    it 'creates a valid email template' do
      email_template = create(:email_template)
      expect(email_template).to be_persisted
      expect(email_template.name).to be_present
      expect(email_template.subject).to be_present
      expect(email_template.content).to be_present
      expect(email_template.category_id).to be_present
    end
  end

  describe 'categories' do
    it 'has 5 categories defined' do
      expect(EmailTemplate::CATEGORIES.size).to eq(5)
    end

    it 'has valid category structure' do
      EmailTemplate::CATEGORIES.each do |category|
        expect(category).to have_key(:id)
        expect(category).to have_key(:name)
        expect(category).to have_key(:color)
        expect(category[:id]).to be_a(Integer)
        expect(category[:name]).to be_a(String)
        expect(category[:color]).to be_a(String)
      end
    end

    it 'has unique category IDs' do
      ids = EmailTemplate::CATEGORIES.map { |c| c[:id] }
      expect(ids.uniq.size).to eq(ids.size)
    end
  end

  describe 'search_data' do
    let(:email_template) { create(:email_template, category_id: 1) }

    it 'returns correct search data structure' do
      search_data = email_template.search_data

      expect(search_data).to have_key(:name)
      expect(search_data).to have_key(:subject)
      expect(search_data).to have_key(:content)
      expect(search_data).to have_key(:category)
      expect(search_data).to have_key(:category_id)
      expect(search_data).to have_key(:category_color)
      expect(search_data).to have_key(:account_id)
      expect(search_data).to have_key(:user_id)
      expect(search_data).to have_key(:is_deleted)
      expect(search_data).to have_key(:created_at)
      expect(search_data).to have_key(:updated_at)
    end

    it 'includes correct category name' do
      search_data = email_template.search_data
      category = EmailTemplate::CATEGORIES.find { |c| c[:id] == email_template.category_id }
      expect(search_data[:category]).to eq(category[:name])
    end

    it 'includes correct category color' do
      search_data = email_template.search_data
      category = EmailTemplate::CATEGORIES.find { |c| c[:id] == email_template.category_id }
      expect(search_data[:category_color]).to eq(category[:color])
    end
  end

  describe 'search_fields' do
    it 'returns correct search fields' do
      expect(EmailTemplate.search_fields).to eq([ :name, :subject, :content, :category ])
    end
  end

  describe 'include_base' do
    it 'includes account and user' do
      expect(EmailTemplate.include_base.includes_values).to include(:account, :user)
    end
  end

  describe 'default_search_order' do
    it 'returns created_at desc' do
      expect(EmailTemplate.default_search_order).to eq({ created_at: :desc })
    end
  end

  describe 'traits' do
    it 'creates deleted template' do
      template = create(:email_template, :deleted)
      expect(template.is_deleted).to be true
    end

    it 'creates approval template' do
      template = create(:email_template, :approval)
      expect(template.category_id).to eq(1)
      expect(template.name).to eq("Email de Aprovação")
    end

    it 'creates rejection template' do
      template = create(:email_template, :rejection)
      expect(template.category_id).to eq(2)
      expect(template.name).to eq("Email de Rejeição")
    end

    it 'creates scheduling template' do
      template = create(:email_template, :scheduling)
      expect(template.category_id).to eq(3)
      expect(template.name).to eq("Email de Agendamento")
    end
  end
end
