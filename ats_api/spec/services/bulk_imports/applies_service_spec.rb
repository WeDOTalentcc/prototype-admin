# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BulkImports::AppliesService do
  describe '.call' do
    let(:schema) { described_class.call }

    it 'returns hash with field definitions' do
      expect(schema).to be_a(Hash)
    end

    it 'includes all candidate fields' do
      candidate_schema = BulkImports::CandidatesService.call

      candidate_schema.each do |field, definition|
        expect(schema[field]).to eq(definition)
      end
    end

    it 'includes required external_job_id field' do
      expect(schema[:external_job_id]).to eq({ label: 'ID Externo da Vaga', required: true })
    end

    it 'includes optional is_deleted field' do
      expect(schema[:is_deleted]).to eq({ label: 'Aplicação Excluída? (true/false)', required: false })
    end

    it 'has more fields than CandidatesService' do
      candidate_fields_count = BulkImports::CandidatesService.call.keys.length

      expect(schema.keys.length).to be > candidate_fields_count
    end

    it 'has exactly 4 required fields' do
      required_fields = schema.select { |_k, v| v[:required] == true }

      expect(required_fields.keys).to match_array([ :name, :email, :external_id, :external_job_id ])
    end
  end
end
