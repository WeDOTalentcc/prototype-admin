# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::ResumeParserService do
  subject(:service) { described_class.new(resume_text, additional_data, ai_provider: ai_provider) }

  let(:resume_text) do
    <<~RESUME
      John Doe
      Software Engineer
      john@example.com | +1234567890

      EXPERIENCE
      Senior Developer at Tech Corp (2020-2023)
      - Led development team
      - Built scalable applications

      EDUCATION
      Bachelor's in Computer Science - MIT (2015-2019)

      SKILLS
      Ruby, Rails, PostgreSQL, AWS
    RESUME
  end

  let(:additional_data) { {} }
  let(:ai_provider) { :gemini }

  describe '#call' do
    context 'when resume text is blank' do
      let(:resume_text) { '' }

      it 'returns error response' do
        result = service.call

        expect(result[:success]).to be false
        expect(result[:error]).to eq('Texto do currículo não fornecido')
      end
    end

    context 'when using Gemini provider' do
      let(:gemini_client) { instance_double(GeminiClient) }
      let(:gemini_response) do
        {
          'choices' => [
            {
              'message' => {
                'content' => '{"name":"John Doe","email":"john@example.com","role_name":"Senior Developer"}'
              }
            }
          ]
        }
      end

      before do
        allow(GeminiClient).to receive(:new).and_return(gemini_client)
        allow(gemini_client).to receive(:chat).and_return(gemini_response)
      end

      it 'parses resume successfully' do
        result = service.call

        expect(result[:success]).to be true
        expect(result[:data]).to be_a(Hash)
        expect(result[:data][:name]).to eq('John Doe')
        expect(result[:data][:email]).to eq('john@example.com')
      end

      it 'calls Gemini with correct parameters' do
        service.call

        expect(gemini_client).to have_received(:chat).with(
          hash_including(
            model: GeminiClient::DEFAULT_CHAT_MODEL,
            temperature: 0.3,
            messages: array_including(
              hash_including(role: 'system'),
              hash_including(role: 'user')
            )
          )
        )
      end

      context 'when response has markdown wrapper' do
        let(:gemini_response) do
          {
            'choices' => [
              {
                'message' => {
                  'content' => "```json\n{\"name\":\"John Doe\"}\n```"
                }
              }
            ]
          }
        end

        it 'removes markdown and parses JSON' do
          result = service.call

          expect(result[:success]).to be true
          expect(result[:data][:name]).to eq('John Doe')
        end
      end

      context 'when response has extra text around JSON' do
        let(:gemini_response) do
          {
            'choices' => [
              {
                'message' => {
                  'content' => 'Here is the result: {"name":"John Doe"} - Done'
                }
              }
            ]
          }
        end

        it 'extracts JSON object correctly' do
          result = service.call

          expect(result[:success]).to be true
          expect(result[:data][:name]).to eq('John Doe')
        end
      end

      context 'when Gemini returns invalid JSON' do
        let(:gemini_response) do
          {
            'choices' => [
              {
                'message' => {
                  'content' => 'Invalid response without JSON'
                }
              }
            ]
          }
        end

        it 'returns error response' do
          result = service.call

          expect(result[:success]).to be false
          expect(result[:error]).to include('Falha ao parsear JSON')
        end
      end

      context 'when Gemini returns empty response' do
        let(:gemini_response) do
          {
            'choices' => [
              {
                'message' => {
                  'content' => ''
                }
              }
            ]
          }
        end

        it 'returns error response' do
          result = service.call

          expect(result[:success]).to be false
          expect(result[:error]).to include('Resposta vazia do Gemini')
        end
      end
    end

    context 'when using OpenAI provider' do
      let(:ai_provider) { :openai }

      # Skip OpenAI tests as service doesn't exist yet
      it 'parses resume successfully', skip: 'OpenaiService not implemented' do
      end

      it 'calls OpenAI with correct parameters', skip: 'OpenaiService not implemented' do
      end

      context 'when OpenAI fails', skip: 'OpenaiService not implemented' do
        it 'returns error response' do
        end
      end
    end

    context 'when additional_data is provided' do
      let(:additional_data) do
        {
          email: 'override@example.com',
          phone: '+9999999999',
          linkedin: 'linkedin.com/in/john',
          location: 'San Francisco, CA, USA'
        }
      end

      let(:gemini_client) { instance_double(GeminiClient) }
      let(:gemini_response) do
        {
          'choices' => [
            {
              'message' => {
                'content' => '{"name":"John Doe"}'
              }
            }
          ]
        }
      end

      before do
        allow(GeminiClient).to receive(:new).and_return(gemini_client)
        allow(gemini_client).to receive(:chat).and_return(gemini_response)
      end

      it 'merges additional data into response' do
        result = service.call

        expect(result[:data][:email]).to eq('override@example.com')
        expect(result[:data][:mobile_phone]).to eq('+9999999999')
        expect(result[:data][:linkedin]).to eq('linkedin.com/in/john')
      end

      it 'splits location into city, state, country' do
        result = service.call

        expect(result[:data][:city]).to eq('San Francisco')
        expect(result[:data][:state]).to eq('CA')
        expect(result[:data][:country]).to eq('USA')
      end

      context 'when location has only city and state' do
        let(:additional_data) { { location: 'Boston, MA' } }

        it 'defaults country to Brasil' do
          result = service.call

          expect(result[:data][:city]).to eq('Boston')
          expect(result[:data][:state]).to eq('MA')
          expect(result[:data][:country]).to eq('Brasil')
        end
      end
    end

    context 'when AI service raises exception' do
      let(:gemini_client) { instance_double(GeminiClient) }

      before do
        allow(GeminiClient).to receive(:new).and_return(gemini_client)
        allow(gemini_client).to receive(:chat).and_raise(StandardError.new('API timeout'))
        allow(Rails.logger).to receive(:error)
      end

      it 'returns error response' do
        result = service.call

        expect(result[:success]).to be false
        expect(result[:error]).to eq('API timeout')
      end

      it 'logs error' do
        service.call

        expect(Rails.logger).to have_received(:error).with(/API timeout/)
      end
    end
  end

  describe 'private methods' do
    describe '#extract_json_from_text' do
      it 'removes markdown wrapper' do
        text = "```json\n{\"key\":\"value\"}\n```"

        result = service.send(:extract_json_from_text, text)

        expect(result).to eq('{"key":"value"}')
      end

      it 'extracts JSON object from mixed text' do
        text = 'Some text {"key":"value"} more text'

        result = service.send(:extract_json_from_text, text)

        expect(result).to eq('{"key":"value"}')
      end

      it 'returns original when no JSON found' do
        text = 'Just plain text'

        result = service.send(:extract_json_from_text, text)

        expect(result).to eq('Just plain text')
      end
    end

    describe '#system_message' do
      it 'includes JSON structure instructions' do
        message = service.send(:system_message)

        expect(message).to include('JSON')
        expect(message).to include('name')
        expect(message).to include('experiences')
        expect(message).to include('educations')
      end

      it 'includes date format instructions' do
        message = service.send(:system_message)

        expect(message).to include('YYYY-MM')
        expect(message).to include('is_current')
      end
    end

    describe '#build_prompt' do
      it 'includes resume text' do
        prompt = service.send(:build_prompt)

        expect(prompt).to include('John Doe')
        expect(prompt).to include('Software Engineer')
      end

      context 'when additional data present' do
        let(:additional_data) { { email: 'test@example.com', phone: '123' } }

        it 'includes additional information' do
          prompt = service.send(:build_prompt)

          expect(prompt).to include('test@example.com')
          expect(prompt).to include('123')
        end
      end

      context 'when no additional data' do
        it 'does not include additional information section' do
          prompt = service.send(:build_prompt)

          expect(prompt).not_to include('Informações adicionais')
        end
      end
    end
  end
end
