# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BulkImports::CandidatesService do
  describe '.call' do
    let(:schema) { described_class.call }

    it 'returns hash with field definitions' do
      expect(schema).to be_a(Hash)
      expect(schema.keys.length).to be > 0
    end

    it 'includes required name field' do
      expect(schema[:name]).to eq({ label: 'Nome Completo', required: true })
    end

    it 'includes required email field' do
      expect(schema[:email]).to eq({ label: 'Email Principal', required: true })
    end

    it 'includes required external_id field' do
      expect(schema[:external_id]).to eq({ label: 'ID Externo do Candidato', required: true })
    end

    it 'includes optional contact fields' do
      expect(schema[:mobile_phone]).to eq({ label: 'Celular', required: false })
      expect(schema[:phone]).to eq({ label: 'Telefone Fixo', required: false })
      expect(schema[:secondary_email]).to eq({ label: 'Email Secundário', required: false })
    end

    it 'includes optional social media fields' do
      expect(schema[:linkedin]).to eq({ label: 'URL do LinkedIn', required: false })
      expect(schema[:github]).to eq({ label: 'URL do GitHub', required: false })
      expect(schema[:portfolio]).to eq({ label: 'URL do Portfólio', required: false })
    end

    it 'includes optional professional fields' do
      expect(schema[:role_name]).to eq({ label: 'Cargo Atual', required: false })
      expect(schema[:current_company]).to eq({ label: 'Empresa Atual', required: false })
      expect(schema[:position_level]).to eq({ label: 'Nível do Cargo', required: false })
    end

    it 'includes optional address fields' do
      expect(schema[:street]).to eq({ label: 'Rua', required: false })
      expect(schema[:city]).to eq({ label: 'Cidade', required: false })
      expect(schema[:state]).to eq({ label: 'Estado (UF)', required: false })
      expect(schema[:zip]).to eq({ label: 'CEP', required: false })
    end

    it 'includes optional salary expectation fields' do
      expect(schema[:desired_salary]).to eq({ label: 'Salário Desejado', required: false })
      expect(schema[:clt_expectation]).to eq({ label: 'Pretensão Salarial (CLT)', required: false })
      expect(schema[:pj_expectation]).to eq({ label: 'Pretensão Salarial (PJ)', required: false })
    end

    it 'has exactly 3 required fields' do
      required_fields = schema.select { |_k, v| v[:required] == true }

      expect(required_fields.keys).to match_array([ :name, :email, :external_id ])
    end

    it 'returns consistent schema across multiple calls' do
      first_call = described_class.call
      second_call = described_class.call

      expect(first_call).to eq(second_call)
    end
  end
end
