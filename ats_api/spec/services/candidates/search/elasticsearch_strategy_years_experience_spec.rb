# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::ElasticsearchStrategy do
  describe '#apply_years_of_experience_range' do
    let(:account) { create(:account) }
    let(:strategy) { described_class.new(account_id: account.id) }

    context 'quando recebe years_of_experience_min e years_of_experience_max' do
      it 'converte para years_of_experience com range' do
        filters = {
          account_id: account.id,
          years_of_experience_min: 5,
          years_of_experience_max: 10,
          city: 'São Paulo'
        }

        result = strategy.send(:apply_years_of_experience_range, filters)

        expect(result[:years_of_experience]).to eq({ gte: 5, lte: 10 })
        expect(result[:years_of_experience_min]).to be_nil
        expect(result[:years_of_experience_max]).to be_nil
        expect(result[:city]).to eq('São Paulo')
      end
    end

    context 'quando recebe apenas years_of_experience_min' do
      it 'cria range apenas com gte' do
        filters = {
          years_of_experience_min: 5
        }

        result = strategy.send(:apply_years_of_experience_range, filters)

        expect(result[:years_of_experience]).to eq({ gte: 5 })
      end
    end

    context 'quando recebe apenas years_of_experience_max' do
      it 'cria range apenas com lte' do
        filters = {
          years_of_experience_max: 10
        }

        result = strategy.send(:apply_years_of_experience_range, filters)

        expect(result[:years_of_experience]).to eq({ lte: 10 })
      end
    end

    context 'quando não recebe filtros de experiência' do
      it 'retorna filtros sem modificação' do
        filters = {
          city: 'São Paulo',
          state: 'SP'
        }

        result = strategy.send(:apply_years_of_experience_range, filters)

        expect(result).to eq(filters)
        expect(result[:years_of_experience]).to be_nil
      end
    end

    context 'quando os valores são strings' do
      it 'converte para inteiros' do
        filters = {
          years_of_experience_min: "5",
          years_of_experience_max: "10"
        }

        result = strategy.send(:apply_years_of_experience_range, filters)

        expect(result[:years_of_experience]).to eq({ gte: 5, lte: 10 })
      end
    end
  end
end
