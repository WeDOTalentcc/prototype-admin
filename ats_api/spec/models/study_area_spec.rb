require 'rails_helper'

RSpec.describe StudyArea, type: :model do
  describe 'associations' do
    it { should belong_to(:account).optional }
  end

  describe 'validations' do
    it { should validate_presence_of(:name) }
  end

  describe 'attributes' do
    it 'defaults approved to false' do
      study_area = StudyArea.new
      expect(study_area.approved).to be(false)
    end
  end
end
