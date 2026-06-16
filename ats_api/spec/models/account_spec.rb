# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Account, type: :model do
  subject { create(:account) }

  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_uniqueness_of(:name).case_insensitive }
  end

  describe 'associations' do
    it { should have_many(:users).dependent(:destroy) }
    it { should have_many(:jobs).dependent(:destroy) }
  end

  describe 'factory' do
    it 'is valid' do
      expect(build(:account)).to be_valid
    end
  end
end
