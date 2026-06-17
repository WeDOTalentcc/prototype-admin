# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Job with Dynamic Field Requirements', type: :model do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe 'field_requirements initialization' do
    context 'when template exists' do
      before do
        JobFieldTemplate.create_default_template(account)
      end

      it 'copies field_requirements from template on create' do
        job = Job.create!(title: "Test Job", account: account, user: user)

        expect(job.field_requirements).to be_an(Array)
        expect(job.field_requirements.length).to be > 0
        expect(job.field_requirements.first).to have_key("field_name")
      end
    end

    context 'when template does not exist' do
      it 'creates default template automatically' do
        expect {
          Job.create!(title: "Test Job", account: account, user: user)
        }.to change { JobFieldTemplate.count }.by(1)
      end
    end
  end

  describe '#make_missing_fields' do
    let!(:template) { JobFieldTemplate.create_default_template(account) }
    let(:job) { Job.create!(title: "Test Job", account: account, user: user) }

    it 'returns missing required fields based on field_requirements' do
      missing = job.make_missing_fields

      expect(missing).to be_an(Array)
      # Deve faltar description (é required no template)
      expect(missing.map { |f| f[:field] }).to include("description")
    end

    it 'does not include fields that are filled' do
      job.update_column(:description, "A great job")
      missing = job.make_missing_fields

      # Description não deve estar na lista de faltantes
      expect(missing.map { |f| f[:field] }).not_to include("description")
    end

    it 'respects custom field_requirements per job' do
      # Customiza os requirements deste job específico
      custom_fields = [
        {
          field_name: "bonus_from",
          label: "Bonus",
          is_required: true,
          category: "critical",
          priority: 1
        }
      ]
      job.update_column(:field_requirements, custom_fields)

      missing = job.make_missing_fields
      expect(missing.map { |f| f[:field] }).to include("bonus_from")
    end
  end

  describe '#completeness_percentage' do
    let!(:template) { JobFieldTemplate.create_default_template(account) }
    let(:job) { Job.create!(title: "Test Job", account: account, user: user) }

    it 'calculates percentage based on field_requirements' do
      percentage = job.completeness_percentage

      expect(percentage).to be_a(Float)
      expect(percentage).to be >= 0
      expect(percentage).to be <= 100
    end

    it 'returns 100% when all required fields are filled' do
      # Simplifica o template para ter apenas title como required
      simple_fields = [
        {
          field_name: "title",
          label: "Title",
          is_required: true,
          category: "critical",
          priority: 1
        }
      ]
      job.update_column(:field_requirements, simple_fields)

      # Title já está preenchido
      expect(job.completeness_percentage).to eq(100.0)
    end
  end

  describe '#is_ready_for_publication?' do
    let!(:template) { JobFieldTemplate.create_default_template(account) }
    let(:job) { Job.create!(title: "Test Job", description: "Test", account: account, user: user) }

    it 'returns false if critical fields are missing' do
      # Template padrão tem vários campos críticos
      expect(job.is_ready_for_publication?).to be(false)
    end

    it 'returns true when all critical fields are filled' do
      # Simplifica para ter apenas title como critical
      simple_fields = [
        {
          field_name: "title",
          label: "Title",
          is_required: true,
          category: "critical",
          priority: 1
        },
        {
          field_name: "description",
          label: "Description",
          is_required: true,
          category: "optional",
          priority: 2
        }
      ]
      job.update_column(:field_requirements, simple_fields)

      expect(job.is_ready_for_publication?).to be(true)
    end
  end
end
