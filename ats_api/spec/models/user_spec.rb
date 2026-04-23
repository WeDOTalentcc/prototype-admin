# spec/models/user_spec.rb
require 'rails_helper'

RSpec.describe User, type: :model do
  # Usamos subject para ter uma instância limpa para testes de unicidade
  subject { create(:user) }

  describe 'validations' do
    it { should validate_presence_of(:email) }
    it { should validate_uniqueness_of(:email).case_insensitive }
    it { should have_secure_password }
  end

  describe 'associations' do
    it { should belong_to(:account).optional }
    it { should have_many(:jobs).dependent(:destroy) }
    # it { should have_many(:roles).through(:user_roles) }
    it { should have_many(:user_roles) }
    it { should have_many(:direct_permissions).through(:user_permissions).source(:permission) }
    it { should have_many(:user_permissions) }
  end

  describe 'factory' do
    it 'is valid' do
      expect(build(:user)).to be_valid
    end
  end
end
