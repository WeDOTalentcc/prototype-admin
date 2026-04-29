# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Feedback, type: :model do
  subject { build(:feedback) }

  describe 'validations' do
    it { should validate_presence_of(:title) }
    it { should validate_presence_of(:description) }
    it { should validate_presence_of(:name) }
  end

  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:job) }
    it { should belong_to(:selective_process) }
  end

  describe 'factory' do
    it 'is valid' do
      expect(build(:feedback)).to be_valid
    end
  end
end
