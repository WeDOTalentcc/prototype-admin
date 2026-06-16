# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BulkImports::JobsService do
  describe '.call' do
    let(:schema) { described_class.call }

    it 'returns hash with field definitions' do
      expect(schema).to be_a(Hash)
      expect(schema.keys.length).to be > 0
    end

    it 'includes required title field' do
      expect(schema[:title]).to eq({ label: 'Título da Vaga', required: true })
    end

    it 'includes optional description field' do
      expect(schema[:description]).to eq({ label: 'Descrição da Vaga', required: false })
    end

    it 'includes location fields' do
      expect(schema[:city]).to eq({ label: 'Cidade', required: false })
      expect(schema[:state]).to eq({ label: 'Estado (UF)', required: false })
      expect(schema[:country]).to eq({ label: 'País', required: false })
    end

    it 'includes workplace type fields' do
      expect(schema[:workplace_type]).to eq({ label: 'Modelo de Trabalho (remoto, híbrido, presencial)', required: false })
      expect(schema[:is_remote]).to eq({ label: 'É 100% Remoto? (true/false)', required: false })
    end

    it 'includes date fields' do
      expect(schema[:published_date]).to eq({ label: 'Data de Publicação', required: false })
      expect(schema[:application_deadline]).to eq({ label: 'Data Limite para Candidatura', required: false })
    end

    it 'includes integration fields' do
      expect(schema[:job_url]).to eq({ label: 'URL da Vaga Original', required: false })
      expect(schema[:provider]).to eq({ label: 'Provedor Externo (ex: Gupy, Catho)', required: false })
      expect(schema[:provider_job_id]).to eq({ label: 'ID da Vaga no Provedor', required: false })
    end

    it 'includes accessibility and badge fields' do
      expect(schema[:disabilities]).to eq({ label: 'Vaga Afirmativa para PCD? (true/false)', required: false })
      expect(schema[:friendly_badge]).to eq({ label: 'Possui Selo "Empresa Amiga"? (true/false)', required: false })
    end

    it 'includes career page fields' do
      expect(schema[:career_page_name]).to eq({ label: 'Nome da Página de Carreiras', required: false })
      expect(schema[:career_page_url]).to eq({ label: 'URL da Página de Carreiras', required: false })
      expect(schema[:career_page_logo]).to eq({ label: 'URL do Logo da Página de Carreiras', required: false })
    end

    it 'has exactly 1 required field' do
      required_fields = schema.select { |_k, v| v[:required] == true }

      expect(required_fields.keys).to eq([ :title ])
    end

    it 'returns consistent schema across multiple calls' do
      first_call = described_class.call
      second_call = described_class.call

      expect(first_call).to eq(second_call)
    end
  end
end
