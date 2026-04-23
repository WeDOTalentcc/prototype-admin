require 'rails_helper'

RSpec.describe PasswordResetToken, type: :model do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe 'validations' do
    it 'is valid with valid attributes' do
      token = PasswordResetToken.new(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now
      )
      expect(token).to be_valid
    end

    it 'is invalid without user' do
      token = PasswordResetToken.new(
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now
      )
      expect(token).not_to be_valid
    end

    it 'is invalid without account' do
      token = PasswordResetToken.new(
        user: user,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now
      )
      expect(token).not_to be_valid
    end

    it 'is invalid without ip_address' do
      token = PasswordResetToken.new(
        user: user,
        account: account,
        expires_at: 1.hour.from_now
      )
      expect(token).not_to be_valid
    end

    it 'is invalid without expires_at' do
      token = PasswordResetToken.new(
        user: user,
        account: account,
        ip_address: '127.0.0.1'
      )
      expect(token).not_to be_valid
    end
  end

  describe 'associations' do
    it { should belong_to(:user) }
    it { should belong_to(:account) }
  end

  describe 'callbacks' do
    it 'generates token on create' do
      token = PasswordResetToken.create!(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now
      )

      expect(token.token_digest).to be_present
      expect(token.raw_token).to be_present
    end

    it 'generates unique token_digest' do
      token1 = PasswordResetToken.create!(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now
      )

      token2 = PasswordResetToken.create!(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now
      )

      expect(token1.token_digest).not_to eq(token2.token_digest)
    end
  end

  describe 'scopes' do
    let!(:valid_token) { PasswordResetToken.create!(
      user: user,
      account: account,
      ip_address: '127.0.0.1',
      expires_at: 1.hour.from_now
    ) }

    let!(:expired_token) { PasswordResetToken.create!(
      user: user,
      account: account,
      ip_address: '127.0.0.1',
      expires_at: 1.hour.ago
    ) }

    let!(:used_token) { PasswordResetToken.create!(
      user: user,
      account: account,
      ip_address: '127.0.0.1',
      expires_at: 1.hour.from_now,
      used_at: Time.current
    ) }

    describe '.valid_tokens' do
      it 'returns only valid, unused tokens' do
        valid_tokens = PasswordResetToken.valid_tokens
        expect(valid_tokens).to include(valid_token)
        expect(valid_tokens).not_to include(expired_token)
        expect(valid_tokens).not_to include(used_token)
      end
    end
  end

  describe '.find_valid' do
    let!(:token) { PasswordResetToken.create!(
      user: user,
      account: account,
      ip_address: '127.0.0.1',
      expires_at: 1.hour.from_now
    ) }

    it 'finds valid token with correct raw token' do
      found_token = PasswordResetToken.find_valid(token.raw_token)
      expect(found_token).to eq(token)
    end

    it 'returns nil for invalid token' do
      found_token = PasswordResetToken.find_valid('invalid_token')
      expect(found_token).to be_nil
    end

    it 'returns nil for expired token' do
      token.update!(expires_at: 1.hour.ago)
      found_token = PasswordResetToken.find_valid(token.raw_token)
      expect(found_token).to be_nil
    end

    it 'returns nil for used token' do
      token.mark_used!
      found_token = PasswordResetToken.find_valid(token.raw_token)
      expect(found_token).to be_nil
    end
  end

  describe '#mark_used!' do
    let(:token) { PasswordResetToken.create!(
      user: user,
      account: account,
      ip_address: '127.0.0.1',
      expires_at: 1.hour.from_now
    ) }

    it 'marks token as used' do
      expect(token.used_at).to be_nil
      token.mark_used!
      expect(token.used_at).to be_present
    end

    it 'persists the used_at timestamp' do
      token.mark_used!
      token.reload
      expect(token.used_at).to be_present
    end
  end
end
