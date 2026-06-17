require 'rails_helper'

RSpec.describe 'V1::PasswordResetTokens API', type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account, email: 'test@example.com') }
  let(:headers) { { 'Content-Type' => 'application/json' } }

  describe 'POST /v1/password_resets' do
    context 'with valid email' do
      it 'creates password reset token and sends email' do
        expect {
          post '/v1/password_resets/', params: {
            email: user.email
          }.to_json, headers: headers
        }.to change(PasswordResetToken, :count).by(1)

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['message']).to eq('Email de redefinição de senha enviado com sucesso')
      end

      it 'invalidates previous unused tokens' do
        # Create an existing token
        existing_token = PasswordResetToken.create!(
          user: user,
          account: account,
          ip_address: '127.0.0.1',
          expires_at: 1.hour.from_now
        )

        post '/v1/password_resets/', params: {
          email: user.email
        }.to_json, headers: headers

        existing_token.reload
        expect(existing_token.used_at).to be_present
      end

      it 'sends email with correct parameters' do
        expect(PasswordResetMailer).to receive(:with).with(
          hash_including(
            user: user,
            token: instance_of(String),
            reset_url: instance_of(String)
          )
        ).and_call_original

        expect_any_instance_of(ActionMailer::MessageDelivery).to receive(:deliver_now)

        post '/v1/password_resets/', params: {
          email: user.email
        }.to_json, headers: headers
      end
    end

    context 'with invalid email' do
      it 'returns error message' do
        post '/v1/password_resets/', params: {
          email: 'nonexistent@example.com'
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include('Email não encontrado')
      end

      it 'does not create token for invalid email' do
        expect {
          post '/v1/password_resets/', params: {
            email: 'nonexistent@example.com'
          }.to_json, headers: headers
        }.not_to change(PasswordResetToken, :count)
      end
    end

    context 'when user has no account' do
      let(:user_without_account) { create(:user, account: nil) }

      it 'returns error when user has no account' do
        post '/v1/password_resets/', params: {
          email: user_without_account.email
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe 'GET /v1/password_resets/:token' do
    let(:token) { PasswordResetToken.create!(
      user: user,
      account: account,
      ip_address: '127.0.0.1',
      expires_at: 1.hour.from_now
    ) }

    context 'with valid token' do
      it 'returns token validation success' do
        get "/v1/password_resets/#{token.raw_token}", headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['message']).to eq('Token válido')
        expect(json['user_email']).to eq(user.email)
        expect(json['expires_at']).to be_present
      end
    end

    context 'with invalid token' do
      it 'returns error message' do
        get '/v1/password_resets/invalid_token', headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include('Token inválido ou expirado')
      end
    end

    context 'with expired token' do
      let(:expired_token) { PasswordResetToken.create!(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.ago
      ) }

      it 'returns error message' do
        get "/v1/password_resets/#{expired_token.raw_token}", headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include('Token inválido ou expirado')
      end
    end

    context 'with used token' do
      let(:used_token) { PasswordResetToken.create!(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now,
        used_at: Time.current
      ) }

      it 'returns error message' do
        get "/v1/password_resets/#{used_token.raw_token}", headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include('Token inválido ou expirado')
      end
    end
  end

  describe 'POST /v1/password_resets/:token/complete' do
    let(:token) { PasswordResetToken.create!(
      user: user,
      account: account,
      ip_address: '127.0.0.1',
      expires_at: 1.hour.from_now
    ) }

    context 'with valid token and password' do
      it 'updates user password and marks token as used' do
        new_password = 'newpassword123'

        post "/v1/password_resets/#{token.raw_token}/complete", params: {
          password: new_password
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['message']).to eq('Senha alterada com sucesso')

        user.reload
        expect(user.authenticate(new_password)).to be_truthy

        token.reload
        expect(token.used_at).to be_present
      end

      it 'does not allow reusing the same token' do
        new_password = 'newpassword123'

        # First use
        post "/v1/password_resets/#{token.raw_token}/complete", params: {
          password: new_password
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)

        # Second attempt
        post "/v1/password_resets/#{token.raw_token}/complete", params: {
          password: 'anotherpassword'
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include('Token inválido ou expirado')
      end
    end

    context 'with invalid token' do
      it 'returns error message' do
        post '/v1/password_resets/invalid_token/complete', params: {
          password: 'newpassword123'
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include('Token inválido ou expirado')
      end
    end

    context 'with invalid password' do
      it 'returns validation errors for too short password' do
        post "/v1/password_resets/#{token.raw_token}/complete", params: {
          password: '12345'
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
      end

      it 'does not mark token as used when password validation fails' do
        post "/v1/password_resets/#{token.raw_token}/complete", params: {
          password: '12345'
        }.to_json, headers: headers

        token.reload
        expect(token.used_at).to be_nil
      end
    end

    context 'with expired token' do
      let(:expired_token) { PasswordResetToken.create!(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.ago
      ) }

      it 'returns error message' do
        post "/v1/password_resets/#{expired_token.raw_token}/complete", params: {
          password: 'newpassword123'
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include('Token inválido ou expirado')
      end
    end
  end

  describe 'Complete Password Reset Flow' do
    it 'allows complete password reset workflow' do
      original_password = 'password123'
      user.update!(password: original_password)

      post '/v1/password_resets/', params: {
        email: user.email
      }.to_json, headers: headers

      expect(response).to have_http_status(:ok)

      reset_token = PasswordResetToken.new(
        user: user,
        account: account,
        ip_address: '127.0.0.1',
        expires_at: 1.hour.from_now
      )
      reset_token.save!
      token_value = reset_token.raw_token

      get "/v1/password_resets/#{token_value}", headers: headers

      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['message']).to eq('Token válido')
      expect(json['user_email']).to eq(user.email)

      new_password = 'brand_new_password_123'
      post "/v1/password_resets/#{token_value}/complete", params: {
        password: new_password
      }.to_json, headers: headers

      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['message']).to eq('Senha alterada com sucesso')

      user.reload
      expect(user.authenticate(new_password)).to be_truthy
      expect(user.authenticate(original_password)).to be_falsey

      reset_token.reload
      expect(reset_token.used_at).to be_present

      post "/v1/password_resets/#{token_value}/complete", params: {
        password: 'another_password_123'
      }.to_json, headers: headers

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
