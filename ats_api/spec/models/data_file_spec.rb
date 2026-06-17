require 'rails_helper'

RSpec.describe DataFile, type: :model do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  before { Current.user = user }
  after  { Current.user = nil }

  describe 'associations' do
    subject { described_class.new }
    it { is_expected.to belong_to(:user).optional }
    it { is_expected.to have_one_attached(:file) }
  end

  describe 'validations' do
    subject { build(:data_file, user: user) }

    it { is_expected.to be_valid }
    it { is_expected.to validate_presence_of(:name) }
  end

  context 'with file attachments' do
    it 'is invalid without an attached file' do
      data_file = described_class.new(name: "Sem arquivo", user: user)
      expect(data_file).not_to be_valid
      expect(data_file.errors[:file]).to include("can't be blank")
    end

    it 'is valid with a supported file type' do
      data_file = build(:data_file, user: user)
      expect(data_file).to be_valid
    end

    it 'is invalid with an unsupported file type' do
      data_file = build(:data_file, user: user)
      unsupported_file = Rack::Test::UploadedFile.new(
        Rails.root.join('spec/support/assets/invalid_file.zip'),
        'application/zip'
      )
      data_file.file.attach(unsupported_file)

      expect(data_file).not_to be_valid
      expect(data_file.errors[:file]).to include(a_string_matching(/has an invalid content type/))
    end
  end

  describe 'callbacks' do
    it 'assigns the current user account_id via AccountScopable on save' do
      data_file = build(:data_file, user: user, account_id: nil)
      data_file.save!
      expect(data_file.reload.account_id).to eq(user.account_id)
    end
  end
end
