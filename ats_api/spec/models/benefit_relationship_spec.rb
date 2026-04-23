require 'rails_helper'

RSpec.describe BenefitRelationship, type: :model do
  subject { build(:benefit_relationship) }

  it { should belong_to(:benefit).optional }
  it { should belong_to(:reference) }

  it { should validate_presence_of(:reference_type) }
  it { should validate_presence_of(:reference_id) }
  it { should validate_presence_of(:name) }
  it { should validate_numericality_of(:days_of_month).only_integer.is_greater_than_or_equal_to(0) }
  it { should validate_numericality_of(:dependents_count).only_integer.is_greater_than_or_equal_to(0) }

  it 'is valid with valid attributes' do
    expect(subject).to be_valid
  end
end
