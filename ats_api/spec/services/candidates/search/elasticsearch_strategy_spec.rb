require 'rails_helper'

RSpec.describe Candidates::Search::ElasticsearchStrategy do
  subject(:strategy) { described_class.new(account_id: account_id) }

  let(:account_id) { 123 }

  describe '#search' do
    let(:es_response) do
      instance_double(
        'Searchkick::Results',
        response: { "hits" => { "hits" => hits } }
      )
    end
    let(:hits) do
      [
        { "_id" => "1", "_score" => 2.5 },
        { "_id" => "2", "_score" => 1.8 }
      ]
    end

    before do
      allow(Candidate).to receive(:search).and_return(es_response)
    end

    it 'returns ranked results with correct structure' do
      result = strategy.search("ruby developer")

      expect(result).to be_an(Array)
      expect(result.size).to eq(2)
      expect(result.first).to include(:id, :rank, :score, :source)
      expect(result.first[:rank]).to eq(1)
      expect(result.first[:id]).to eq(1)
      expect(result.first[:score]).to eq(2.5)
    end

    it 'filters by account_id and is_deleted' do
      expect(Candidate).to receive(:search).with(
        "ruby",
        hash_including(where: { account_id: account_id, is_deleted: false })
      )

      strategy.search("ruby")
    end

    it 'merges custom filters' do
      filters = { city: "são paulo", skills: [ "ruby" ] }

      expect(Candidate).to receive(:search).with(
        "developer",
        hash_including(where: hash_including(
          account_id: account_id,
          is_deleted: false,
          city: "são paulo",
          skills: [ "ruby" ]
        ))
      )

      strategy.search("developer", user_filters: filters)
    end

    it 'returns empty array on error' do
      allow(Candidate).to receive(:search).and_raise(StandardError.new("ES error"))
      allow(Rails.logger).to receive(:error)

      result = strategy.search("ruby")

      expect(result).to eq([])
    end

    it 'limits results to initial_pool_size' do
      pool_size = 200
      allow(Candidates::Search::Configuration).to receive(:initial_pool_size).and_return(pool_size)

      expect(Candidate).to receive(:search).with(
        "*",
        hash_including(per_page: pool_size)
      )

      strategy.search("*")
    end

    it 'returns empty array for blank query' do
      result = strategy.search("")

      expect(result).to eq([])
    end
  end
end
