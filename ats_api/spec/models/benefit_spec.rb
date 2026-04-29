require 'rails_helper'

RSpec.describe Benefit, type: :model do
  subject { build(:benefit) }

  it { should validate_presence_of(:name) }
  it { should validate_numericality_of(:days_of_month).only_integer.is_greater_than_or_equal_to(0) }

  it 'is valid with valid attributes' do
    expect(subject).to be_valid
  end
end
