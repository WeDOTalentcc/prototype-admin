# frozen_string_literal: true

require 'rails_helper'

RSpec.describe CandidateService::EmbeddingService do
  subject(:service) { described_class.new(candidate.id) }

  let(:account) { create(:account) }
  let(:candidate) { create(:candidate, account: account, name: 'John Doe', role_name: 'Developer') }
  let(:text_builder) { double('TextBuilder') }
  let(:encoder) { instance_double(Embeddings::Encoder) }
  let(:embedding_vector) { Array.new(768) { rand } }
  let(:namespace) { 'test_namespace' }

  describe '#call' do
    context 'in test environment' do
      it 'returns nil without processing' do
        result = service.call

        expect(result).to be_nil
      end
    end

    context 'in non-test environment', skip: true do
      before do
        allow(Rails.env).to receive(:test?).and_return(false)
        allow(CandidateService::TextBuilder).to receive(:call).with(candidate).and_return('Generated text')
        allow(Embeddings::Encoder).to receive(:new).and_return(encoder)
        allow(encoder).to receive(:call).and_return(embedding_vector)
        allow(VectorStores::Namespaces).to receive(:for_account).and_return(namespace)
      end

      it 'builds text using TextBuilder' do
        service.call

        expect(CandidateService::TextBuilder).to have_received(:call).with(candidate)
      end

      it 'generates embedding from text' do
        service.call

        expect(encoder).to have_received(:call).with('Generated text')
      end

      it 'gets namespace for account' do
        service.call

        expect(VectorStores::Namespaces).to have_received(:for_account)
          .with(candidate.account_id, :candidates)
      end

      context 'when text is blank' do
        before do
          allow(CandidateService::TextBuilder).to receive(:call).and_return('')
        end

        it 'raises error' do
          expect {
            service.call
          }.to raise_error(/texto vazio para embedding/)
        end
      end

      context 'when embedding vector is empty' do
        before do
          allow(encoder).to receive(:call).and_return(nil)
        end

        it 'raises error' do
          expect {
            service.call
          }.to raise_error(/embedding vazio/)
        end
      end
    end
  end
end
