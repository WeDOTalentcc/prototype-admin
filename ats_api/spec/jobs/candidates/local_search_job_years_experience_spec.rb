# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::LocalSearchJob, type: :job do
  describe '#apply_years_of_experience_filter' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:sourcing) { create(:sourcing, account: account, user: user) }
    let(:job_instance) { described_class.new }

    before do
      job_instance.instance_variable_set(:@account, account)
      job_instance.instance_variable_set(:@user, user)
      job_instance.instance_variable_set(:@return_sourced, false)
    end

    context 'quando recebe years_of_experience com gte e lte' do
      it 'converte para years_of_experience_min e years_of_experience_max' do
        input = {
          years_of_experience: { gte: 5, lte: 10 }
        }

        result = job_instance.send(:apply_years_of_experience_filter, input)

        expect(result[:years_of_experience_min]).to eq(5)
        expect(result[:years_of_experience_max]).to eq(10)
        expect(result[:years_of_experience]).to be_nil
      end
    end

    context 'quando recebe apenas gte' do
      it 'converte apenas years_of_experience_min' do
        input = {
          years_of_experience: { gte: 5 }
        }

        result = job_instance.send(:apply_years_of_experience_filter, input)

        expect(result[:years_of_experience_min]).to eq(5)
        expect(result[:years_of_experience_max]).to be_nil
      end
    end

    context 'quando recebe apenas lte' do
      it 'converte apenas years_of_experience_max' do
        input = {
          years_of_experience: { lte: 10 }
        }

        result = job_instance.send(:apply_years_of_experience_filter, input)

        expect(result[:years_of_experience_min]).to be_nil
        expect(result[:years_of_experience_max]).to eq(10)
      end
    end

    context 'quando não recebe years_of_experience' do
      it 'retorna os filtros sem modificação' do
        input = { city: 'São Paulo' }

        result = job_instance.send(:apply_years_of_experience_filter, input)

        expect(result).to eq(input)
      end
    end

    context 'quando years_of_experience não é um hash' do
      it 'retorna os filtros sem modificação' do
        input = { years_of_experience: 5 }

        result = job_instance.send(:apply_years_of_experience_filter, input)

        expect(result).to eq(input)
      end
    end

    context 'quando recebe chaves como strings' do
      it 'converte corretamente' do
        input = {
          years_of_experience: { "gte" => 5, "lte" => 10 }
        }

        result = job_instance.send(:apply_years_of_experience_filter, input)

        expect(result[:years_of_experience_min]).to eq(5)
        expect(result[:years_of_experience_max]).to eq(10)
      end
    end
  end

  describe '#build_sourced_profile_sourcings_where' do
    let(:job_instance) { described_class.new }

    context 'quando recebe years_of_experience_min e years_of_experience_max' do
      it 'mapeia para total_experience_years com range' do
        input = {
          years_of_experience_min: 5,
          years_of_experience_max: 10,
          city: 'São Paulo'
        }

        result = job_instance.send(:build_sourced_profile_sourcings_where, input)

        expect(result[:total_experience_years]).to eq({ gte: 5, lte: 10 })
        expect(result[:city]).to eq('São Paulo')
      end
    end

    context 'quando recebe apenas years_of_experience_min' do
      it 'mapeia apenas gte' do
        input = { years_of_experience_min: 5 }

        result = job_instance.send(:build_sourced_profile_sourcings_where, input)

        expect(result[:total_experience_years]).to eq({ gte: 5 })
      end
    end

    context 'quando recebe apenas years_of_experience_max' do
      it 'mapeia apenas lte' do
        input = { years_of_experience_max: 10 }

        result = job_instance.send(:build_sourced_profile_sourcings_where, input)

        expect(result[:total_experience_years]).to eq({ lte: 10 })
      end
    end

    context 'quando não recebe filtros de experiência' do
      it 'não adiciona total_experience_years' do
        input = { city: 'São Paulo' }

        result = job_instance.send(:build_sourced_profile_sourcings_where, input)

        expect(result[:total_experience_years]).to be_nil
        expect(result[:city]).to eq('São Paulo')
      end
    end
  end
end
