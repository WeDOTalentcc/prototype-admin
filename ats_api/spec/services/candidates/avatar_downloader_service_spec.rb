# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::AvatarDownloaderService, type: :service do
  let(:account) { Account.new(id: 1) }
  let(:candidate) do
    instance_double(
      Candidate,
      id: 123,
      account: account,
      avatar: avatar_attachment
    )
  end
  let(:avatar_attachment) { instance_double(ActiveStorage::Attached::One, attached?: false) }
  let(:valid_image_url) { 'https://media.licdn.com/dms/image/v2/D4D03AQGwnX0vEDRxdg/profile-displayphoto-crop_800_800/profile.jpg' }
  let(:invalid_url) { 'not-a-valid-url' }
  let(:service) { described_class.new(candidate, valid_image_url) }

  describe '#call' do
    context 'when image URL is blank' do
      let(:service) { described_class.new(candidate, nil) }

      it 'returns error' do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("URL da imagem não informada")
      end
    end

    context 'when URL is invalid' do
      let(:service) { described_class.new(candidate, invalid_url) }

      it 'returns error' do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("URL inválida")
      end
    end

    context 'when candidate already has avatar' do
      let(:avatar_attachment) { instance_double(ActiveStorage::Attached::One, attached?: true) }

      it 'returns error indicating avatar already exists' do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("Avatar já existe")
      end
    end

    context 'when URL is valid and candidate has no avatar' do
      let(:image_data) { 'fake-image-data' }
      let(:downloaded_file) { double('file', content_type: 'image/jpeg') }

      before do
        allow(URI).to receive(:open).with(valid_image_url, read_timeout: 10).and_return(downloaded_file)
        allow(avatar_attachment).to receive(:attach)
      end

      it 'downloads and attaches avatar successfully' do
        result = service.call

        expect(result[:success]).to be true
        expect(result[:filename]).to be_present
        expect(avatar_attachment).to have_received(:attach)
      end

      it 'generates unique filename with timestamp' do
        result = service.call

        expect(result[:filename]).to match(/avatar_123_\d+\.(jpg|jpeg)/)
      end
    end

    context 'when HTTP error occurs while downloading image' do
      before do
        allow(URI).to receive(:open).and_raise(OpenURI::HTTPError.new('404 Not Found', nil))
      end

      it 'returns error' do
        result = service.call

        expect(result[:success]).to be false
        expect(result[:error]).to include("Erro ao baixar imagem")
      end
    end

    context 'when timeout occurs in request' do
      before do
        allow(URI).to receive(:open).and_raise(Timeout::Error.new('execution expired'))
      end

      it 'returns error' do
        result = service.call

        expect(result[:success]).to be false
        expect(result[:error]).to include("Erro inesperado")
      end
    end
  end
end
