# frozen_string_literal: true

require 'rails_helper'

RSpec.describe JobFieldTemplate, type: :model do
  let(:account) { create(:account) }

  describe 'validations' do
    it { should belong_to(:account) }
    it { should validate_presence_of(:name) }
    it { should validate_presence_of(:account_id) }
    it { should validate_presence_of(:fields) }
  end

  describe '.default_for_account' do
    it 'returns the default template for an account' do
      template = JobFieldTemplate.create_default_template(account)

      found_template = JobFieldTemplate.default_for_account(account.id)
      expect(found_template).to eq(template)
      expect(found_template.is_default).to be(true)
    end
  end

  describe '.create_default_template' do
    it 'creates a default template with standard fields' do
      template = JobFieldTemplate.create_default_template(account)

      expect(template).to be_persisted
      expect(template.is_default).to be(true)
      expect(template.fields).to be_an(Array)
      expect(template.fields.length).to be > 10

      # Verifica alguns campos importantes
      field_names = template.fields.map { |f| f["field_name"] }
      expect(field_names).to include("title", "description", "salary_from", "workplace_type")
    end
  end

  describe '.default_fields' do
    it 'returns an array of field definitions' do
      fields = JobFieldTemplate.default_fields

      expect(fields).to be_an(Array)
      expect(fields.first).to have_key(:field_name)
      expect(fields.first).to have_key(:label)
      expect(fields.first).to have_key(:is_required)
      expect(fields.first).to have_key(:category)
      expect(fields.first).to have_key(:priority)
      expect(fields.first).to have_key(:job_journey_position)
    end
  end

  describe 'fields validation' do
    it 'validates fields structure' do
      template = JobFieldTemplate.new(
        account: account,
        name: "Test Template",
        fields: [ { field_name: "title" } ] # Faltando campos obrigatórios
      )

      expect(template).not_to be_valid
      expect(template.errors[:fields]).to be_present
    end

    it 'accepts valid fields structure' do
      template = JobFieldTemplate.new(
        account: account,
        name: "Test Template",
        fields: [
          {
            field_name: "title",
            label: "Job Title",
            is_required: true,
            category: "critical",
            priority: 1
          }
        ]
      )

      expect(template).to be_valid
    end
  end
end
