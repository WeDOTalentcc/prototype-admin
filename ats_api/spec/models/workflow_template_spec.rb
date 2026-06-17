require 'rails_helper'

RSpec.describe WorkflowTemplate, type: :model do
  describe 'factory' do
    it 'has a valid factory' do
      expect(build(:workflow_template)).to be_valid
    end
  end

  describe 'associations' do
    # it { should belong_to(:user) }
    it { should belong_to(:account) }
  end

  describe 'validations' do
    it { should validate_presence_of(:name) }
  end
end
