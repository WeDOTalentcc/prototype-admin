# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::QueryParserService do
  subject(:service) { described_class.new(model: model) }

  let(:model) { 'gemini-2.5-flash' }

  describe '.call' do
    it 'creates instance and calls method' do
      allow_any_instance_of(described_class).to receive(:call).and_return({ search: '*' })

      result = described_class.call('test query')

      expect(result).to eq({ search: '*' })
    end
  end

  describe '#call' do
    context 'in test environment' do
      it 'returns fallback response' do
        result = service.call('ruby developer')

        expect(result).to eq({
          search: 'ruby developer',
          where: {},
          order: {}
        })
      end
    end

    context 'when text is blank' do
      it 'returns fallback with wildcard search' do
        result = service.call('')

        expect(result).to eq({
          search: '*',
          where: {},
          order: {}
        })
      end
    end

    context 'in non-test environment', skip: true do
      let(:client) { instance_double(GeminiClient) }
      let(:valid_response) do
        {
          'choices' => [
            {
              'message' => {
                'content' => '{"search":"*","where":{"skills":{"in":["ruby","rails"]}},"order":{}}'
              }
            }
          ]
        }
      end

      before do
        allow(Rails.env).to receive(:test?).and_return(false)
        allow(GeminiClient).to receive(:new).and_return(client)
        allow(client).to receive(:chat).and_return(valid_response)
        allow(Rails.logger).to receive(:info)
      end

      it 'calls Gemini API with correct parameters' do
        service.call('ruby developer')

        expect(client).to have_received(:chat).with(
          hash_including(
            model: 'gemini-2.5-flash',
            temperature: 0.2,
            max_tokens: 1500,
            response_format: { type: 'json_object' },
            messages: array_including(
              hash_including(role: 'system'),
              hash_including(role: 'user')
            )
          )
        )
      end

      it 'parses response correctly' do
        result = service.call('ruby developer')

        expect(result).to include(
          search: '*',
          where: { skills: { in: [ 'ruby', 'rails' ] } },
          order: {}
        )
      end

      it 'logs parsing activity' do
        service.call('ruby developer')

        expect(Rails.logger).to have_received(:info).with(/Parsing/)
        expect(Rails.logger).to have_received(:info).with(/Result/)
      end

      context 'when response has markdown wrapper' do
        let(:valid_response) do
          {
            'choices' => [
              {
                'message' => {
                  'content' => "```json\n{\"search\":\"*\",\"where\":{},\"order\":{}}\n```"
                }
              }
            ]
          }
        end

        it 'removes markdown and parses correctly' do
          result = service.call('test')

          expect(result[:search]).to eq('*')
        end
      end

      context 'when API returns nil content' do
        let(:valid_response) do
          {
            'choices' => [
              {
                'message' => {
                  'content' => nil
                }
              }
            ]
          }
        end

        it 'returns fallback response' do
          result = service.call('test query')

          expect(result).to eq({
            search: 'test query',
            where: {},
            order: {}
          })
        end
      end

      context 'when API raises error' do
        before do
          allow(client).to receive(:chat).and_raise(StandardError.new('API error'))
          allow(Rails.logger).to receive(:error)
        end

        it 'returns fallback response' do
          result = service.call('test query')

          expect(result).to eq({
            search: 'test query',
            where: {},
            order: {}
          })
        end

        it 'logs error' do
          service.call('test query')

          expect(Rails.logger).to have_received(:error).with(/API error/)
        end
      end
    end
  end

  describe 'private methods' do
    describe '#fallback_response' do
      it 'returns search with text when present' do
        result = service.send(:fallback_response, 'test query')

        expect(result).to eq({
          search: 'test query',
          where: {},
          order: {}
        })
      end

      it 'returns wildcard search when text is blank' do
        result = service.send(:fallback_response, '')

        expect(result).to eq({
          search: '*',
          where: {},
          order: {}
        })
      end
    end

    describe '#parse_response' do
      it 'parses valid JSON response' do
        content = '{"search":"*","where":{"city":"são paulo"},"order":{}}'

        result = service.send(:parse_response, content)

        expect(result).to eq({
          search: '*',
          where: { city: 'são paulo' },
          order: {}
        })
      end

      it 'removes markdown code blocks' do
        content = "```json\n{\"search\":\"*\"}\n```"

        result = service.send(:parse_response, content)

        expect(result[:search]).to eq('*')
      end

      it 'normalizes where values to lowercase' do
        content = '{"search":"*","where":{"city":"SÃO PAULO","skills":["RUBY","Rails"]}}'

        result = service.send(:parse_response, content)

        expect(result[:where][:city]).to eq('são paulo')
        expect(result[:where][:skills]).to eq([ 'ruby', 'rails' ])
      end

      it 'handles nested operators' do
        content = '{"search":"*","where":{"salary":{"gte":5000,"lte":10000}}}'

        result = service.send(:parse_response, content)

        expect(result[:where][:salary]).to eq({ gte: 5000, lte: 10000 })
      end

      it 'provides defaults for missing fields' do
        content = '{}'

        result = service.send(:parse_response, content)

        expect(result).to eq({
          search: '*',
          where: {},
          order: {}
        })
      end
    end

    describe '#normalize_where' do
      it 'returns empty hash when where is blank' do
        result = service.send(:normalize_where, nil)

        expect(result).to eq({})
      end

      it 'downcases string values' do
        where = { city: 'São Paulo', state: 'SP' }

        result = service.send(:normalize_where, where)

        expect(result[:city]).to eq('são paulo')
        expect(result[:state]).to eq('sp')
      end

      it 'downcases array values' do
        where = { skills: [ 'Ruby', 'RAILS', 'PostgreSQL' ] }

        result = service.send(:normalize_where, where)

        expect(result[:skills]).to eq([ 'ruby', 'rails', 'postgresql' ])
      end

      it 'handles nested hash operators' do
        where = { salary: { gte: 5000 }, name: { ilike: '%John%' } }

        result = service.send(:normalize_where, where)

        expect(result[:salary]).to eq({ gte: 5000 })
        expect(result[:name]).to eq({ ilike: '%john%' })
      end

      it 'preserves non-string values' do
        where = { age: 25, active: true, salary: { gte: 5000 } }

        result = service.send(:normalize_where, where)

        expect(result[:age]).to eq(25)
        expect(result[:active]).to be true
        expect(result[:salary][:gte]).to eq(5000)
      end
    end

    describe '#system_prompt' do
      it 'includes available fields' do
        prompt = service.send(:system_prompt)

        expect(prompt).to include('name')
        expect(prompt).to include('skills')
        expect(prompt).to include('city')
        expect(prompt).to include('remote_work')
      end

      it 'includes operators documentation' do
        prompt = service.send(:system_prompt)

        expect(prompt).to include('ilike')
        expect(prompt).to include('in')
        expect(prompt).to include('gte')
      end

      it 'includes examples' do
        prompt = service.send(:system_prompt)

        expect(prompt).to include('desenvolvedores ruby')
        expect(prompt).to include('gerente de projetos')
      end

      it 'specifies JSON-only output' do
        prompt = service.send(:system_prompt)

        expect(prompt).to include('JSON')
        expect(prompt).to include('minúsculas')
      end
    end

    describe '#user_prompt' do
      it 'formats user query' do
        result = service.send(:user_prompt, 'ruby developer')

        expect(result).to include('ruby developer')
        expect(result).to include('Converta em JSON')
      end
    end
  end
end
