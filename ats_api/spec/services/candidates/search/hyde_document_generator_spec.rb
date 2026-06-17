# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::HydeDocumentGenerator do
  let(:llm_client) { instance_double(GeminiClient) }
  subject(:generator) { described_class.new(llm_client: llm_client) }

  describe '#generate' do
    context 'when profile is blank' do
      it 'returns empty string for nil' do
        expect(generator.generate(nil)).to eq('')
      end

      it 'returns empty string for empty hash' do
        expect(generator.generate({})).to eq('')
      end
    end

    context 'when generating resume document' do
      let(:profile) do
        {
          "seniority" => "senior",
          "years_experience" => 8,
          "primary_role" => "Backend Developer",
          "industry" => "fintech",
          "core_technologies" => [ "Ruby on Rails", "PostgreSQL", "Redis", "Elasticsearch" ],
          "transferable_skills" => [ "problem solving", "team collaboration" ]
        }
      end

      it 'generates standard verbosity document' do
        result = generator.generate(profile, context: :resume, verbosity: :standard)

        expect(result).to include('senior')
        expect(result).to include('8 anos de experiência')
        expect(result).to include('Backend Developer')
        expect(result).to include('fintech')
      end

      it 'includes technology stack' do
        result = generator.generate(profile, context: :resume, verbosity: :standard)

        expect(result).to include('Ruby on Rails')
        expect(result).to include('PostgreSQL')
      end

      it 'includes transferable skills' do
        result = generator.generate(profile, context: :resume, verbosity: :standard)

        expect(result).to include('problem solving')
      end

      it 'generates concise document when requested' do
        result = generator.generate(profile, context: :resume, verbosity: :concise)

        expect(result).to include('senior')
        expect(result).to include('Backend Developer')
        expect(result.length).to be < 300
      end

      it 'defaults context to resume' do
        result = generator.generate(profile)

        expect(result).to include('Backend Developer')
      end
    end

    context 'when generating job description document' do
      let(:profile) do
        {
          "seniority" => "pleno",
          "years_experience" => 4,
          "primary_role" => "Frontend Developer",
          "industry" => "e-commerce",
          "core_technologies" => [ "React", "TypeScript", "Next.js" ],
          "transferable_skills" => [ "UI/UX design", "responsive design" ]
        }
      end

      it 'generates standard verbosity document' do
        result = generator.generate(profile, context: :job_description, verbosity: :standard)

        expect(result).to include('Frontend Developer')
        expect(result).to include('pleno')
        expect(result).to include('e-commerce')
      end

      it 'includes required skills' do
        result = generator.generate(profile, context: :job_description, verbosity: :standard)

        expect(result).to include('React')
        expect(result).to include('TypeScript')
      end

      it 'includes nice to have skills' do
        result = generator.generate(profile, context: :job_description, verbosity: :standard)

        expect(result).to include('UI/UX design')
      end

      it 'generates concise document when requested' do
        result = generator.generate(profile, context: :job_description, verbosity: :concise)

        expect(result).to include('Frontend Developer')
        expect(result.length).to be < 200
      end

      it 'calculates experience range' do
        result = generator.generate(profile, context: :job_description, verbosity: :standard)

        expect(result).to include('anos')
        expect(result).to include('Experiência')
      end
    end

    context 'when profile has minimal data' do
      let(:minimal_profile) { { "primary_role" => "Developer" } }

      it 'uses default values for missing fields' do
        result = generator.generate(minimal_profile, context: :resume)

        expect(result).to include('pleno')
        expect(result).to include('5 anos de experiência')
        expect(result).to include('tecnologia')
      end

      it 'handles empty technologies array' do
        result = generator.generate(minimal_profile, context: :resume)

        expect(result).to be_a(String)
        expect(result).not_to be_empty
      end
    end

    context 'when detecting distributed systems tech' do
      let(:distributed_profile) do
        {
          "core_technologies" => [ "Ruby", "Redis", "Kafka", "Elasticsearch" ],
          "primary_role" => "Backend Engineer"
        }
      end

      it 'identifies distributed architecture context' do
        result = generator.generate(distributed_profile, context: :resume)

        expect(result).to include('sistemas distribuídos')
      end
    end

    context 'when detecting web development tech' do
      let(:web_profile) do
        {
          "core_technologies" => [ "React", "Next.js", "Node.js" ],
          "primary_role" => "Full Stack Developer"
        }
      end

      it 'identifies web development context' do
        result = generator.generate(web_profile, context: :resume)

        expect(result).to include('web full-stack')
      end
    end

    context 'when detecting data processing tech' do
      let(:data_profile) do
        {
          "core_technologies" => [ "Python", "Spark", "Airflow", "ETL" ],
          "primary_role" => "Data Engineer"
        }
      end

      it 'identifies data processing context' do
        result = generator.generate(data_profile, context: :resume)

        expect(result).to include('processamento de dados')
      end
    end

    context 'when deriving soft skills based on seniority' do
      it 'assigns leadership skills to senior level' do
        profile = { "seniority" => "senior", "primary_role" => "Developer" }
        result = generator.generate(profile, context: :resume)

        expect(result).to include('liderança')
      end

      it 'assigns team collaboration to pleno level' do
        profile = { "seniority" => "pleno", "primary_role" => "Developer" }
        result = generator.generate(profile, context: :resume)

        expect(result).to include('trabalho em equipe')
      end

      it 'assigns learning focus to junior level' do
        profile = { "seniority" => "junior", "primary_role" => "Developer" }
        result = generator.generate(profile, context: :resume)

        expect(result).to include('aprendizado')
      end
    end

    context 'when profile has many technologies' do
      let(:tech_heavy_profile) do
        {
          "core_technologies" => [ "Ruby", "Rails", "PostgreSQL", "Redis", "Sidekiq", "RSpec", "Docker" ],
          "primary_role" => "Backend Developer"
        }
      end

      it 'splits technologies between primary and secondary' do
        result = generator.generate(tech_heavy_profile, context: :resume)

        expect(result).to include('Ruby')
        expect(result).to include('Rails')
      end

      it 'includes all technologies in tech list' do
        result = generator.generate(tech_heavy_profile, context: :resume)

        expect(result).to include('Docker')
        expect(result).to include('RSpec')
      end
    end
  end
end
