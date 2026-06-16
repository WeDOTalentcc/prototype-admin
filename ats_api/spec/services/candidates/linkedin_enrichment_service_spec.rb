# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::LinkedinEnrichmentService, type: :service do
  let(:candidate) { create(:candidate, linkedin: "john-doe", role_name: nil) }
  let(:service) { described_class.new(candidate) }

  let(:linkedin_data) do
    {
      basic_info: {
        headline: "Senior Software Engineer",
        about: "Passionate about clean code and SOLID principles",
        location: {
          full: "São Paulo, São Paulo, Brazil"
        },
        top_skills: [ "Ruby on Rails", "React", "PostgreSQL" ]
      },
      experiences: [
        {
          is_current: true,
          company: "Tech Company",
          title: "Senior Software Engineer"
        }
      ],
      educations: [
        {
          school: "USP",
          degree: "Bachelor",
          field_of_study: "Computer Science"
        }
      ]
    }
  end

  describe '#call' do
    context 'with valid linkedin URL' do
      before do
        allow_any_instance_of(Apify::LinkedinProfileParserService).to receive(:parse)
          .and_return([ linkedin_data ])
      end

      it 'returns success result' do
        result = service.call

        expect(result.success?).to be true
        expect(result.error).to be_nil
      end

      it 'enriches candidate with linkedin data' do
        service.call

        candidate.reload
        expect(candidate.role_name).to eq("Senior Software Engineer")
        expect(candidate.self_introduction).to include("Passionate about")
        expect(candidate.city).to eq("São Paulo")
        expect(candidate.state).to eq("São Paulo")
        expect(candidate.country).to eq("Brazil")
        expect(candidate.current_company).to eq("Tech Company")
      end

      it 'adds linkedin skills' do
        service.call

        candidate.reload
        expect(candidate.linkedin_skills).to include("Ruby on Rails")
        expect(candidate.linkedin_skills).to include("React")
      end

      it 'updates linkedin_enriched_at' do
        expect {
          service.call
          candidate.reload
        }.to change(candidate, :linkedin_enriched_at).from(nil)
      end

      it 'returns updated fields' do
        result = service.call

        expect(result.updated_fields).to include(:role_name)
        expect(result.updated_fields).to include(:city)
        expect(result.updated_fields).to include(:linkedin_skills)
      end
    end

    context 'with blank linkedin URL' do
      let(:candidate) { create(:candidate, linkedin: nil) }

      it 'returns failure result' do
        result = service.call

        expect(result.success?).to be false
        expect(result.error).to eq("LinkedIn URL não informada")
      end
    end

    context 'with invalid linkedin URL' do
      let(:candidate) { create(:candidate, linkedin: "invalid-url") }

      it 'returns failure result' do
        result = service.call

        expect(result.success?).to be false
        expect(result.error).to eq("URL do LinkedIn inválida")
      end
    end

    context 'when apify returns error' do
      before do
        allow_any_instance_of(Apify::LinkedinProfileParserService).to receive(:parse)
          .and_return([ { error: "Profile not found" } ])
      end

      it 'returns failure result' do
        result = service.call

        expect(result.success?).to be false
        expect(result.error).to eq("Profile not found")
      end
    end

    context 'when rate limited' do
      before do
        retry_after = Time.current + 1.hour
        error = Apify::LinkedinProfileParserService::RateLimitError.new(
          "Rate limited",
          retry_after: retry_after
        )
        allow_any_instance_of(Apify::LinkedinProfileParserService).to receive(:parse)
          .and_raise(error)
      end

      it 'returns failure result with retry message' do
        result = service.call

        expect(result.success?).to be false
        expect(result.error).to include("Rate limit")
        expect(result.error).to include("minutos")
      end
    end
  end
end
