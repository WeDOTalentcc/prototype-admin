# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::QueryAnalyzer do
  let(:llm_client) { instance_double(GeminiClient) }
  subject(:analyzer) { described_class.new(llm_client: llm_client) }

  describe '#analyze' do
    let(:query_text) { 'senior ruby developer' }

    before do
      allow(Rails.cache).to receive(:read).and_return(nil)
      allow(Rails.cache).to receive(:write)
    end

    context 'when query is blank' do
      it 'returns passthrough analysis' do
        result = analyzer.analyze('')

        expect(result).to be_a(Candidates::Search::QueryAnalysis)
        expect(result.original_query).to eq('')
        expect(result.confidence).to eq(1.0)
      end

      it 'does not call LLM' do
        expect(llm_client).not_to receive(:chat)

        analyzer.analyze(nil)
      end
    end

    context 'when cached result exists' do
      let(:cached_data) do
        {
          original_query: query_text,
          entities: { role: 'developer', seniority: 'senior' },
          expanded_terms: [ 'ruby on rails', 'rails' ],
          keyword_query: 'senior ruby developer',
          embedding_query: 'experienced Ruby developer',
          confidence: 0.85
        }
      end

      before do
        allow(Rails.cache).to receive(:read).and_return(cached_data)
      end

      it 'returns cached analysis' do
        result = analyzer.analyze(query_text)

        expect(result.entities[:role]).to eq('developer')
        expect(result.confidence).to eq(0.85)
      end

      it 'does not call LLM' do
        expect(llm_client).not_to receive(:chat)

        analyzer.analyze(query_text)
      end
    end

    context 'when LLM returns valid response' do
      let(:llm_response) do
        {
          "choices" => [
            {
              "message" => {
                "content" => {
                  entities: { role: 'developer', skills: [ 'ruby', 'rails' ], seniority: 'senior' },
                  expanded_terms: [ 'ruby on rails', 'ror' ],
                  keyword_query: 'senior ruby rails developer',
                  embedding_query: 'Senior Ruby on Rails developer with 5+ years',
                  confidence: 0.9
                }.to_json
              }
            }
          ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it 'parses and returns analysis' do
        result = analyzer.analyze(query_text)

        expect(result.entities[:role]).to eq('developer')
        expect(result.entities[:skills]).to eq([ 'ruby', 'rails' ])
        expect(result.keyword_query).to eq('senior ruby rails developer')
        expect(result.confidence).to eq(0.9)
      end

      it 'stores result in cache' do
        expect(Rails.cache).to receive(:write).with(
          anything,
          hash_including(
            original_query: query_text,
            confidence: 0.9
          ),
          expires_in: 1.hour
        )

        analyzer.analyze(query_text)
      end

      it 'uses correct cache key format' do
        expected_key = /^query_analysis:[a-f0-9]{16}$/

        expect(Rails.cache).to receive(:read).with(match(expected_key))

        analyzer.analyze(query_text)
      end
    end

    context 'when LLM returns response with code blocks' do
      let(:llm_response) do
        {
          "choices" => [
            {
              "message" => {
                "content" => "```json\n{\"entities\": {}, \"expanded_terms\": [], \"keyword_query\": \"test\", \"embedding_query\": \"test\", \"confidence\": 0.8}\n```"
              }
            }
          ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it 'strips code blocks and parses JSON' do
        result = analyzer.analyze(query_text)

        expect(result.keyword_query).to eq('test')
        expect(result.confidence).to eq(0.8)
      end
    end

    context 'when LLM times out' do
      before do
        allow(llm_client).to receive(:chat).and_raise(Timeout::Error)
      end

      it 'returns passthrough analysis' do
        result = analyzer.analyze(query_text)

        expect(result.original_query).to eq(query_text)
        expect(result.embedding_query).to eq(query_text)
        expect(result.confidence).to eq(1.0)
      end

      it 'logs timeout warning' do
        expect(Rails.logger).to receive(:warn).with(/Timeout/)

        analyzer.analyze(query_text)
      end
    end

    context 'when LLM returns invalid JSON' do
      let(:llm_response) do
        {
          "choices" => [
            { "message" => { "content" => "invalid json {" } }
          ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it 'returns passthrough analysis' do
        result = analyzer.analyze(query_text)

        expect(result.embedding_query).to eq(query_text)
        expect(result.confidence).to eq(1.0)
      end

      it 'logs parse error' do
        expect(Rails.logger).to receive(:warn).with(/JSON parse failed/)

        analyzer.analyze(query_text)
      end
    end

    context 'when cache read fails' do
      before do
        allow(Rails.cache).to receive(:read).and_raise(StandardError.new('Redis down'))
        allow(llm_client).to receive(:chat).and_return(
          {
            "choices" => [
              {
                "message" => {
                  "content" => { entities: {}, expanded_terms: [], keyword_query: 'test', embedding_query: 'test', confidence: 0.5 }.to_json
                }
              }
            ]
          }
        )
      end

      it 'continues with LLM call' do
        expect(Rails.logger).to receive(:warn).with(/Cache read failed/)

        result = analyzer.analyze(query_text)

        expect(result).to be_a(Candidates::Search::QueryAnalysis)
      end
    end

    context 'when cache write fails' do
      let(:llm_response) do
        {
          "choices" => [
            {
              "message" => {
                "content" => { entities: {}, expanded_terms: [], keyword_query: 'test', embedding_query: 'test', confidence: 0.5 }.to_json
              }
            }
          ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
        allow(Rails.cache).to receive(:write).and_raise(StandardError.new('Redis down'))
      end

      it 'logs warning but returns result' do
        expect(Rails.logger).to receive(:warn).with(/Cache write failed/)

        result = analyzer.analyze(query_text)

        expect(result.keyword_query).to eq('test')
      end
    end

    context 'when unexpected error occurs' do
      before do
        allow(llm_client).to receive(:chat).and_raise(StandardError.new('Network error'))
      end

      it 'returns passthrough analysis' do
        result = analyzer.analyze(query_text)

        expect(result.embedding_query).to eq(query_text)
      end

      it 'logs error' do
        expect(Rails.logger).to receive(:error).with(/Failed/)

        analyzer.analyze(query_text)
      end
    end
  end
end

RSpec.describe Candidates::Search::QueryAnalysis do
  describe '.passthrough' do
    it 'creates analysis with original query' do
      result = described_class.passthrough('ruby dev')

      expect(result.original_query).to eq('ruby dev')
      expect(result.embedding_query).to eq('ruby dev')
      expect(result.entities).to eq({})
      expect(result.expanded_terms).to eq([])
      expect(result.confidence).to eq(1.0)
    end
  end

  describe '#use_expanded?' do
    it 'returns true when confidence >= 0.7 and has expanded terms' do
      analysis = described_class.new(
        original_query: 'test',
        entities: {},
        expanded_terms: [ 'term1' ],
        embedding_query: 'test',
        confidence: 0.8
      )

      expect(analysis.use_expanded?).to be true
    end

    it 'returns false when confidence < 0.7' do
      analysis = described_class.new(
        original_query: 'test',
        entities: {},
        expanded_terms: [ 'term1' ],
        embedding_query: 'test',
        confidence: 0.6
      )

      expect(analysis.use_expanded?).to be false
    end

    it 'returns false when no expanded terms' do
      analysis = described_class.new(
        original_query: 'test',
        entities: {},
        expanded_terms: [],
        embedding_query: 'test',
        confidence: 0.9
      )

      expect(analysis.use_expanded?).to be false
    end
  end

  describe '#elasticsearch_query' do
    it 'returns keyword_query when present' do
      analysis = described_class.new(
        original_query: 'original',
        entities: {},
        expanded_terms: [],
        keyword_query: 'optimized',
        embedding_query: 'test',
        confidence: 0.8
      )

      expect(analysis.elasticsearch_query).to eq('optimized')
    end

    it 'returns original_query when keyword_query is blank' do
      analysis = described_class.new(
        original_query: 'original',
        entities: {},
        expanded_terms: [],
        keyword_query: '',
        embedding_query: 'test',
        confidence: 0.8
      )

      expect(analysis.elasticsearch_query).to eq('original')
    end
  end
end
