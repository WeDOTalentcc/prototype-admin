require 'rails_helper'

RSpec.describe User, type: :model do
  subject { build(:user) }

  it { should belong_to(:account).optional }

  it { should validate_presence_of(:email) }
  it { should validate_uniqueness_of(:email).case_insensitive }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end

  describe '#authenticate' do
    let(:user) { create(:user, password: 'secret') }

    it 'returns the user when password is correct' do
      expect(user.authenticate('secret')).to eq(user)
    end

    it 'returns false when password is incorrect' do
      expect(user.authenticate('wrong')).to eq(false)
    end
  end
end
