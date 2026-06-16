# frozen_string_literal: true

require 'rails_helper'

RSpec.describe SourcedProfileSourcings::SearchService do
  subject(:service) do
    described_class.new(
      query: query,
      account_id: account_id,
      where: where,
      limit: limit
    )
  end

  let(:account_id) { 123 }
  let(:query) { "desenvolvedor ruby" }
  let(:where) { {} }
  let(:limit) { 50 }

  describe '.call' do
    let(:search_results) do
      instance_double(
        'Searchkick::Results',
        total_count: 10
      )
    end

    before do
      allow(SourcedProfileSourcing).to receive(:search).and_return(search_results)
      allow(Rails.logger).to receive(:info)
    end

    it 'busca em SourcedProfileSourcing' do
      expect(SourcedProfileSourcing).to receive(:search).with(
        query,
        hash_including(
          fields: array_including("curriculum_text^5", "role_name^3", "name^2"),
          where: hash_including(
            account_id: account_id,
            is_deleted: false
          ),
          limit: limit,
          load: false
        )
      )

      described_class.call(
        query: query,
        account_id: account_id,
        where: where,
        limit: limit
      )
    end

    it 'retorna os resultados da busca' do
      result = described_class.call(
        query: query,
        account_id: account_id,
        where: where,
        limit: limit
      )

      expect(result).to eq(search_results)
    end

    it 'faz merge com filtros adicionais' do
      custom_where = { city: "São Paulo", state: "SP" }

      expect(SourcedProfileSourcing).to receive(:search).with(
        query,
        hash_including(
          where: hash_including(
            account_id: account_id,
            is_deleted: false,
            city: "São Paulo",
            state: "SP"
          )
        )
      )

      described_class.call(
        query: query,
        account_id: account_id,
        where: custom_where,
        limit: limit
      )
    end

    it 'usa campos com pesos corretos' do
      expect(SourcedProfileSourcing).to receive(:search).with(
        query,
        hash_including(
          fields: [
            "curriculum_text^5",
            "role_name^3",
            "name^2",
            "summary^2",
            "current_company^2",
            "skills",
            "expertise",
            "recent_roles",
            "education_institutions",
            "study_areas"
          ]
        )
      )

      described_class.call(
        query: query,
        account_id: account_id,
        where: where,
        limit: limit
      )
    end

    it 'ordena por score' do
      expect(SourcedProfileSourcing).to receive(:search).with(
        query,
        hash_including(order: { _score: :desc })
      )

      described_class.call(
        query: query,
        account_id: account_id,
        where: where,
        limit: limit
      )
    end

    it 'não carrega registros do banco' do
      expect(SourcedProfileSourcing).to receive(:search).with(
        query,
        hash_including(load: false)
      )

      described_class.call(
        query: query,
        account_id: account_id,
        where: where,
        limit: limit
      )
    end

    context 'quando ocorre erro' do
      before do
        allow(SourcedProfileSourcing).to receive(:search).and_raise(StandardError.new("ES error"))
        allow(Rails.logger).to receive(:error)
      end

      it 'propaga o erro' do
        expect {
          described_class.call(
            query: query,
            account_id: account_id,
            where: where,
            limit: limit
          )
        }.to raise_error(StandardError, "ES error")
      end
    end
  end

  describe '#call' do
    let(:search_results) do
      instance_double('Searchkick::Results', total_count: 5)
    end

    before do
      allow(SourcedProfileSourcing).to receive(:search).and_return(search_results)
      allow(Rails.logger).to receive(:info)
    end

    it 'retorna resultados da busca' do
      result = service.call
      expect(result).to eq(search_results)
    end
  end

  describe 'with empty where' do
    let(:where) { nil }
    let(:search_results) do
      instance_double('Searchkick::Results', total_count: 0)
    end

    before do
      allow(SourcedProfileSourcing).to receive(:search).and_return(search_results)
      allow(Rails.logger).to receive(:info)
    end

    it 'trata where como hash vazio' do
      expect(SourcedProfileSourcing).to receive(:search).with(
        query,
        hash_including(
          where: hash_including(
            account_id: account_id,
            is_deleted: false
          )
        )
      )

      service.call
    end
  end
end
