require 'rails_helper'

RSpec.describe Company, type: :model do
  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:user).optional }
    it { should have_one_attached(:logo) }
  end

  describe 'validations' do
    subject { create(:company) }

    it 'allows blank name' do
      company = build(:company, name: nil)
      expect(company).to be_valid
    end

    it 'validates uniqueness of name scoped to account_id, ignoring case and non-deleted records' do
      account = create(:account)
      create(:company, name: "Empresa X", account: account)

      duplicate = build(:company, name: "empresa x", account: account)
      expect(duplicate).to be_invalid
      expect(duplicate.errors[:name]).to include("Empresa já cadastrada")
    end

    it 'allows same name in different accounts' do
      create(:company, name: "Acme", account: create(:account))
      company = build(:company, name: "Acme", account: create(:account))
      expect(company).to be_valid
    end

    it 'allows same name in same account if previous is deleted' do
      account = create(:account)
      company1 = create(:company, name: "TechCorp", account: account, is_deleted: true)
      Company.reindex(refresh: true)
      company2 = build(:company, name: "TechCorp", account: account, is_deleted: false)
      expect(company2).to be_valid
    end
  end

  describe 'logo attachment' do
    it 'attaches a logo file' do
      company = build(:company)
      file = fixture_file_upload(Rails.root.join('spec/support/assets/test_image.png'), 'image/png')
      company.logo.attach(file)

      expect(company.logo).to be_attached
      expect(company.logo.filename.to_s).to eq('test_image.png')
    end
  end
end
