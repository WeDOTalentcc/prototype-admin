# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Sourcings::JobEnqueuerService do
  describe '#apply_years_of_experience_to_custom_filters' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:sourcing) { create(:sourcing, account: account, user: user) }
    let(:service) do
      described_class.new(
        user: user,
        sourcing: sourcing,
        query: "desenvolvedor Ruby",
        params: {}
      )
    end

    context 'quando where contém years_of_experience' do
      it 'move para custom_filters.years_experience' do
        params = {
          where: {
            years_of_experience: { gte: 5, lte: 10 },
            city: 'São Paulo'
          }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result[:custom_filters][:years_experience]).to eq({ min: 5, max: 10 })
        expect(result[:where][:years_of_experience]).to be_nil
        expect(result[:where][:city]).to eq('São Paulo')
      end
    end

    context 'quando years_of_experience tem apenas gte' do
      it 'adiciona apenas min aos custom_filters' do
        params = {
          where: {
            years_of_experience: { gte: 5 }
          }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result[:custom_filters][:years_experience]).to eq({ min: 5 })
      end
    end

    context 'quando years_of_experience tem apenas lte' do
      it 'adiciona apenas max aos custom_filters' do
        params = {
          where: {
            years_of_experience: { lte: 10 }
          }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result[:custom_filters][:years_experience]).to eq({ max: 10 })
      end
    end

    context 'quando where não contém years_of_experience' do
      it 'retorna params sem modificação' do
        params = {
          where: { city: 'São Paulo' }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result[:custom_filters]).to be_nil
        expect(result[:where]).to eq(params[:where])
      end
    end

    context 'quando years_of_experience não é um hash' do
      it 'retorna params sem modificação' do
        params = {
          where: { years_of_experience: 5 }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result).to eq(params)
      end
    end

    context 'quando where usa chaves string' do
      it 'converte corretamente' do
        params = {
          where: {
            "years_of_experience" => { "gte" => 5, "lte" => 10 }
          }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result[:custom_filters][:years_experience]).to eq({ min: 5, max: 10 })
      end
    end

    context 'quando where fica vazio após remoção' do
      it 'remove a chave where' do
        params = {
          where: {
            years_of_experience: { gte: 5, lte: 10 }
          }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result[:where]).to be_nil
        expect(result[:custom_filters][:years_experience]).to eq({ min: 5, max: 10 })
      end
    end

    context 'quando já existem custom_filters' do
      it 'mescla com os custom_filters existentes' do
        params = {
          where: {
            years_of_experience: { gte: 5, lte: 10 }
          },
          custom_filters: {
            locations: [ "Brasil" ]
          }
        }

        result = service.send(:apply_years_of_experience_to_custom_filters, params)

        expect(result[:custom_filters][:years_experience]).to eq({ min: 5, max: 10 })
        expect(result[:custom_filters][:locations]).to eq([ "Brasil" ])
      end
    end
  end
end
