require 'rails_helper'

RSpec.describe LanguageRelationship, type: :model do
  subject { build(:language_relationship) }

  it { should belong_to(:language) }
  it { should belong_to(:reference) }

  it { should validate_presence_of(:reference_type) }
  it { should validate_presence_of(:reference_id) }
  it { should validate_presence_of(:priority) }

  it 'is valid with valid attributes' do
    expect(subject).to be_valid
  end

  it 'is invalid if min_value > max_value' do
    subject.min_value = 10
    subject.max_value = 5
    expect(subject).not_to be_valid
    expect(subject.errors[:min_value]).to include('não pode ser maior que max_value')
  end

  it 'is valid when min_value and max_value are nil' do
    subject.min_value = nil
    subject.max_value = nil
    expect(subject).to be_valid
  end

  describe 'level validation' do
    it 'accepts valid levels' do
      %w[basico intermediario avancado fluente nativo].each do |lvl|
        subject.level = lvl
        expect(subject).to be_valid
      end
    end

    it 'rejects invalid level' do
      subject.level = 'invalid'
      expect(subject).not_to be_valid
      expect(subject.errors[:level]).to be_present
    end
  end
end
