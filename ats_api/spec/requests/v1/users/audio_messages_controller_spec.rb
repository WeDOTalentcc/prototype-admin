require 'rails_helper'

RSpec.describe V1::Users::AudioMessagesController, type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  let(:authentication_headers) { auth_headers(user) }

  describe 'POST /v1/users/audio_messages' do
    let(:valid_params) do
      {
        audio_message: {
          audio_data: 'base64_encoded_audio_data_here',
          audio_format: 'wav',
          audio_duration: 5.2,
          transcription: 'Olá, preciso de ajuda com recrutamento'
        }
      }
    end

    before do
      # Mock RabbitMQ connection
      connection = instance_double(Bunny::Session)
      channel = instance_double(Bunny::Channel)
      exchange = instance_double(Bunny::Exchange)

      allow(Bunny).to receive(:new).and_return(connection)
      allow(connection).to receive(:start)
      allow(connection).to receive(:close)
      allow(connection).to receive(:create_channel).and_return(channel)
      allow(channel).to receive(:direct).and_return(exchange)
      allow(exchange).to receive(:publish)
    end

    context 'when authenticated with valid params' do
      before do
        post '/v1/users/audio_messages', params: valid_params, headers: authentication_headers
      end

      it 'creates a new audio message' do
        expect(response).to have_http_status(:accepted)
        expect(Message.count).to eq(1)

        message = Message.last
        expect(message.content).to eq('Olá, preciso de ajuda com recrutamento')
        expect(message.entity).to eq(Message::ROLE_USER)
        expect(message.reference_id).to eq(user.id)
        expect(message.account_id).to eq(account.id)
        expect(message.metadata['is_audio']).to be true
        expect(message.metadata['audio_format']).to eq('wav')
        expect(message.metadata['audio_duration']).to eq(5.2)
      end

      it 'returns success message with message_id' do
        json = JSON.parse(response.body)
        expect(json['data']['message']).to include('sendo processada')
        expect(json['data']['message_id']).to be_present
      end

      it 'publishes to RabbitMQ queue' do
        connection = instance_double(Bunny::Session)
        channel = instance_double(Bunny::Channel)
        exchange = instance_double(Bunny::Exchange)

        allow(Bunny).to receive(:new).and_return(connection)
        allow(connection).to receive(:start)
        allow(connection).to receive(:close)
        allow(connection).to receive(:create_channel).and_return(channel)
        allow(channel).to receive(:direct).and_return(exchange)
        allow(exchange).to receive(:publish)

        post '/v1/users/audio_messages', params: valid_params, headers: authentication_headers

        expect(exchange).to have_received(:publish).with(
          kind_of(String), # JSON payload
          routing_key: "audio_messages_created",
          persistent: true,
          headers: hash_including(
            message_type: "audio_message",
            user_id: user.id
          )
        )
      end
    end

    context 'when authenticated with minimal params' do
      let(:minimal_params) do
        {
          audio_message: {
            audio_data: 'base64_audio_data'
          }
        }
      end

      before do
        post '/v1/users/audio_messages', params: minimal_params, headers: authentication_headers
      end

      it 'creates message with default values' do
        expect(response).to have_http_status(:accepted)

        message = Message.last
        expect(message.content).to eq('[Mensagem de áudio]')
        expect(message.metadata['audio_format']).to eq('wav')
      end
    end

    context 'when not authenticated' do
      before do
        post '/v1/users/audio_messages', params: valid_params
      end

      it 'returns unauthorized' do
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'when params are invalid' do
      let(:invalid_params) do
        {
          audio_message: {
            # Missing audio_data
            audio_format: 'wav'
          }
        }
      end

      before do
        post '/v1/users/audio_messages', params: invalid_params, headers: authentication_headers
      end

      it 'returns unprocessable entity' do
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when RabbitMQ connection fails' do
      before do
        allow(Bunny).to receive(:new).and_raise(StandardError.new("Connection failed"))
        post '/v1/users/audio_messages', params: valid_params, headers: authentication_headers
      end

      it 'returns error response' do
        expect(response).to have_http_status(:unprocessable_entity)

        json = JSON.parse(response.body)
        expect(json['errors']['message']).to include('Erro ao processar')
      end
    end
  end

  describe 'GET /v1/users/audio_messages/:id' do
    let!(:audio_message) do
      create(:message,
        reference_id: user.id,
        reference_type: "User",
        account: account,
        content: 'Mensagem de áudio transcrita',
        metadata: { is_audio: true, audio_format: 'wav' }
      )
    end

    context 'when authenticated and message exists' do
      before do
        get "/v1/users/audio_messages/#{audio_message.id}", headers: authentication_headers
      end

      it 'returns the audio message' do
        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body)
        expect(json['data']['id']).to eq(audio_message.id)
        expect(json['data']['content']).to eq('Mensagem de áudio transcrita')
        expect(json['data']['metadata']['is_audio']).to be true
      end
    end

    context 'when message belongs to different user' do
      let!(:other_user) { create(:user) }
      let!(:other_message) do
        create(:message,
          reference_id: other_user.id,
          reference_type: "User",
          account: other_user.account
        )
      end

      before do
        get "/v1/users/audio_messages/#{other_message.id}", headers: authentication_headers
      end

      it 'returns not found' do
        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when message does not exist' do
      before do
        get '/v1/users/audio_messages/999999', headers: authentication_headers
      end

      it 'returns not found' do
        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      before do
        get "/v1/users/audio_messages/#{audio_message.id}"
      end

      it 'returns unauthorized' do
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
