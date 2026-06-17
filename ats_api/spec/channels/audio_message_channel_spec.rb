require 'rails_helper'

RSpec.describe AudioMessageChannel, type: :channel do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  before do
    stub_connection current_user: user
  end

  describe '#subscribed' do
    context 'with valid user_id' do
      it 'subscribes to audio messages stream' do
        subscribe(user_id: user.id)

        expect(subscription).to be_confirmed
        expect(subscription).to have_stream_from("audio_messages_user_#{user.id}")
      end
    end

    context 'with invalid user_id' do
      it 'does not subscribe' do
        subscribe(user_id: 999999)

        expect(subscription).to be_confirmed
        expect(subscription).not_to have_stream_from("audio_messages_user_#{user.id}")
      end
    end
  end

  describe '#receive' do
    before do
      subscribe(user_id: user.id)
    end

    context 'with audio message data' do
      let(:audio_message_data) do
        {
          'type' => 'audio_message',
          'audio_data' => 'base64_encoded_audio_data',
          'audio_format' => 'wav',
          'audio_duration' => 5.0,
          'transcription' => 'Olá, como você pode me ajudar?'
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

      it 'creates a message and publishes to queue' do
        expect {
          perform :receive, audio_message_data
        }.to change(Message, :count).by(1)

        message = Message.last
        expect(message.content).to eq('Olá, como você pode me ajudar?')
        expect(message.entity).to eq(Message::ROLE_USER)
        expect(message.reference_id).to eq(user.id)
        expect(message.metadata['is_audio']).to be true
        expect(message.metadata['audio_format']).to eq('wav')
      end

      it 'sends confirmation to client' do
        perform :receive, audio_message_data

        expect(transmissions).to include(
          hash_including(
            'type' => 'audio_received',
            'status' => 'processing'
          )
        )
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

        perform :receive, audio_message_data

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

    context 'with non-audio message' do
      let(:regular_message_data) do
        {
          'type' => 'text_message',
          'content' => 'Esta é uma mensagem de texto'
        }
      end

      it 'does not process the message' do
        expect {
          perform :receive, regular_message_data
        }.not_to change(Message, :count)
      end
    end

    context 'when an error occurs' do
      let(:audio_message_data) do
        {
          'type' => 'audio_message',
          'audio_data' => 'invalid_base64_data'
        }
      end

      before do
        allow(Message).to receive(:create!).and_raise(StandardError.new("Database error"))
      end

      it 'sends error message to client' do
        perform :receive, audio_message_data

        expect(transmissions).to include(
          hash_including(
            'type' => 'error',
            'message' => 'Erro ao processar mensagem de áudio'
          )
        )
      end
    end
  end

  describe '#unsubscribed' do
    it 'stops all streams' do
      subscribe(user_id: user.id)
      expect(subscription).to have_stream_from("audio_messages_user_#{user.id}")

      unsubscribe
      expect(subscription).not_to have_streams
    end
  end
end
