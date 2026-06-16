# spec/models/candidate_spec.rb
require 'rails_helper'

RSpec.describe Candidate, type: :model do
  subject { build(:candidate) }

  it { should validate_presence_of(:name) }
  it { should validate_presence_of(:email) }
  it { should validate_uniqueness_of(:email) }
  # it { should validate_uniqueness_of(:cpf).allow_blank }

  # it { should belong_to(:city).optional }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end
