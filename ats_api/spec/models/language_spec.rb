require 'rails_helper'

RSpec.describe Language, type: :model do
  subject { build(:language) }

  it { should validate_presence_of(:name) }
  it { should validate_uniqueness_of(:name).case_insensitive }
  it { should validate_presence_of(:acronym) }
  it { should validate_uniqueness_of(:acronym).case_insensitive }
  it { should validate_presence_of(:name_ptbr) }

  it 'is valid with valid attributes' do
    expect(subject).to be_valid
  end
end
