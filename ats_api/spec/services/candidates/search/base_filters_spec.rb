# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::BaseFilters do
  subject(:base_filters) { described_class.new(account_id: account_id) }

  let(:account_id) { 123 }

  describe '#to_hash' do
    it 'returns mandatory base filters' do
      result = base_filters.to_hash

      expect(result).to include(
        account_id: 123,
        is_deleted: false
      )
    end

    it 'includes has_curriculum when configured' do
      allow(Candidates::Search::Configuration).to receive(:require_curriculum_text?).and_return(true)

      result = base_filters.to_hash

      expect(result).to include(has_curriculum: true)
    end

    it 'does not include has_curriculum when disabled' do
      allow(Candidates::Search::Configuration).to receive(:require_curriculum_text?).and_return(false)

      result = base_filters.to_hash

      expect(result).not_to have_key(:has_curriculum)
    end

    it 'returns frozen hash (immutable)' do
      result = base_filters.to_hash

      expect(result).to be_frozen
    end

    it 'NUNCA permite sobrescrever account_id' do
      result = base_filters.to_hash

      expect { result[:account_id] = 999 }.to raise_error(FrozenError)
    end

    it 'NUNCA permite sobrescrever is_deleted' do
      result = base_filters.to_hash

      expect { result[:is_deleted] = true }.to raise_error(FrozenError)
    end
  end

  describe '#base_scope' do
    it 'applies filters to default relation (Candidate)' do
      relation = instance_double('ActiveRecord::Relation')
      filtered_relation = instance_double('ActiveRecord::Relation')

      allow(Candidate).to receive(:where).with(account_id: 123).and_return(relation)
      allow(relation).to receive(:where).with(is_deleted: false).and_return(filtered_relation)

      result = base_filters.base_scope

      expect(result).to eq(filtered_relation)
    end

    it 'accepts custom relation as parameter' do
      custom_relation = instance_double('ActiveRecord::Relation')
      filtered1 = instance_double('ActiveRecord::Relation')
      filtered2 = instance_double('ActiveRecord::Relation')

      allow(custom_relation).to receive(:where).with(account_id: 123).and_return(filtered1)
      allow(filtered1).to receive(:where).with(is_deleted: false).and_return(filtered2)

      result = base_filters.base_scope(custom_relation)

      expect(result).to eq(filtered2)
    end

    it 'ALWAYS filters by constructor account_id' do
      relation = double('Relation')

      expect(Candidate).to receive(:where).with(account_id: 123).and_return(relation)
      allow(relation).to receive(:where).with(is_deleted: false).and_return(relation)

      base_filters.base_scope
    end

    it 'SEMPRE filtra is_deleted = false' do
      relation = double('Relation')

      allow(Candidate).to receive(:where).with(account_id: 123).and_return(relation)
      expect(relation).to receive(:where).with(is_deleted: false).and_return(relation)

      base_filters.base_scope
    end
  end
end
