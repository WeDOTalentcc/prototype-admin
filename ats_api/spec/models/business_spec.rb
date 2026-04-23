require 'rails_helper'

RSpec.describe Business, type: :model do
  subject { build(:business) }

  describe 'validations' do
    it { is_expected.to validate_presence_of(:name) }
  end

  describe 'associations' do
    it { is_expected.to belong_to(:account) }
  end
end
