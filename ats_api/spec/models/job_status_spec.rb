require 'rails_helper'

RSpec.describe JobStatus, type: :model do
  subject { described_class.new(name: 'Ativo', color: '#00FF00') }

  it { should validate_presence_of(:name) }
  it { should validate_uniqueness_of(:name).case_insensitive }
  it { should validate_presence_of(:color) }

  it { should have_many(:jobs).dependent(:nullify) }

  it 'is valid with valid attributes' do
    expect(subject).to be_valid
  end

  it 'is invalid without a name' do
    subject.name = nil
    expect(subject).not_to be_valid
  end

  it 'is invalid without a color' do
    subject.color = nil
    expect(subject).not_to be_valid
  end
end
