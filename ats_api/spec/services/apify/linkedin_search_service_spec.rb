# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Apify::LinkedinSearchService do
  let(:http_client) { instance_double('HttpClient', post: nil, get: nil) }
  let(:logger) { instance_double(Logger, info: nil, debug: nil, warn: nil, error: nil) }
  subject(:service) { described_class.new(client: http_client, logger: logger) }

  describe '.search' do
    it 'creates instance and delegates to #search' do
      allow_any_instance_of(described_class).to receive(:search).and_return(
        double(profiles: [], query: nil, run_metadata: {})
      )

      result = described_class.search(keywords: 'ruby developer')

      expect(result).to respond_to(:profiles)
    end
  end

  describe '.builder' do
    it 'returns QueryBuilder instance' do
      builder = described_class.builder

      expect(builder).to respond_to(:with_query)
      expect(builder).to respond_to(:in_locations)
    end
  end

  describe '#search' do
    let(:query_options) { { keywords: 'ruby developer', locations: [ 'Brazil' ] } }
    let(:run_id) { 'run_abc123' }

    context 'when search succeeds' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:completed_response) { { data: { id: run_id, status: 'SUCCEEDED', statusMessage: 'Done' } } }
      let(:results) { [ { name: 'John Doe', linkedin_url: 'https://linkedin.com/in/johndoe' } ] }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(completed_response, results)
      end

      it 'returns ResultSet with profiles' do
        result = service.search(**query_options)

        expect(result).to respond_to(:profiles)
        expect(result.profiles.map(&:to_h)).to eq(results.map { |p| p.transform_keys(&:to_sym) })
      end

      it 'logs search start' do
        expect(logger).to receive(:info).with(/Starting/)

        service.search(**query_options)
      end

      it 'logs completion' do
        expect(logger).to receive(:info).with(/Completed: 1 profiles/)

        service.search(**query_options)
      end

      it 'starts actor run with correct payload' do
        expect(http_client).to receive(:post).with(
          'acts/harvestapi~linkedin-profile-search/runs',
          anything
        )

        service.search(**query_options)
      end

      it 'fetches results from completed run' do
        expect(http_client).to receive(:get).with("actor-runs/#{run_id}/dataset/items")

        service.search(**query_options)
      end
    end

    context 'when query is invalid' do
      it 'raises ArgumentError for empty criteria' do
        expect { service.search }.to raise_error(ArgumentError, /No search criteria/)
      end
    end

    context 'when run is still running' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:running_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:completed_response) { { data: { id: run_id, status: 'SUCCEEDED' } } }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(
          running_response,
          running_response,
          completed_response,
          []
        )
        allow(service).to receive(:sleep)
      end

      it 'polls until completion' do
        expect(http_client).to receive(:get).with("actor-runs/#{run_id}").at_least(:twice)

        service.search(**query_options)
      end

      it 'logs polling attempts' do
        expect(logger).to receive(:debug).with(/Polling/).at_least(:twice)

        service.search(**query_options)
      end
    end

    context 'when run fails' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:failed_response) { { data: { id: run_id, status: 'FAILED', statusMessage: 'Actor crashed' } } }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(failed_response)
      end

      it 'raises RunFailedError' do
        expect { service.search(**query_options) }.to raise_error(/Actor crashed/)
      end
    end

    context 'when rate limited' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:rate_limit_response) { { data: { id: run_id, status: 'FAILED', statusMessage: 'rate limited' } } }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(rate_limit_response)
      end

      it 'raises RateLimitError' do
        expect { service.search(**query_options) }.to raise_error(/rate limit/)
      end
    end

    context 'when run times out' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:timeout_response) { { data: { id: run_id, status: 'TIMED-OUT' } } }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(timeout_response)
      end

      it 'raises TimeoutError' do
        expect { service.search(**query_options) }.to raise_error(/timed out/)
      end
    end

    context 'when run is aborted' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:aborted_response) { { data: { id: run_id, status: 'ABORTED' } } }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(aborted_response)
      end

      it 'raises AbortedError' do
        expect { service.search(**query_options) }.to raise_error(/aborted/)
      end
    end

    context 'when polling exceeds max attempts' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:running_response) { { data: { id: run_id, status: 'RUNNING' } } }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(running_response)
        allow(service).to receive(:sleep)
      end

      it 'raises TimeoutError after 120 attempts' do
        expect { service.search(**query_options) }.to raise_error(/timeout after 10 minutes/)
      end
    end

    context 'when HTTP client returns nil for results' do
      let(:start_response) { { data: { id: run_id, status: 'RUNNING' } } }
      let(:completed_response) { { data: { id: run_id, status: 'SUCCEEDED' } } }

      before do
        allow(http_client).to receive(:post).and_return(start_response)
        allow(http_client).to receive(:get).and_return(completed_response, nil)
      end

      it 'returns empty profiles array' do
        result = service.search(**query_options)

        expect(result.profiles).to eq([])
      end
    end
  end
end
