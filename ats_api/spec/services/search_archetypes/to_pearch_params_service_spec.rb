require 'rails_helper'

RSpec.describe SearchArchetypes::ToPearchParamsService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe '.call' do
    context 'with basic archetype' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          name: 'Ruby Developer',
          query: 'Ruby on Rails Developer',
          seniority: :mid,
          min_experience_years: 3,
          skills: [ 'Ruby', 'Rails', 'PostgreSQL' ],
          languages: [ 'Português', 'Inglês' ],
          location: 'São Paulo, SP',
          industry: 'Technology'
        )
      end

      it 'builds complete query string' do
        result = described_class.call(archetype: archetype)

        expect(result[:query]).to include('Ruby on Rails Developer')
        expect(result[:query]).to include('Pleno level')
        expect(result[:query]).to include('3+ years of experience')
        expect(result[:query]).to include('from São Paulo, SP')
        expect(result[:query]).to include('with skills in Ruby, Rails, PostgreSQL')
        expect(result[:query]).to include('speaking Português and Inglês')
        expect(result[:query]).to include('in Technology industry')
      end

      it 'builds custom_filters hash' do
        result = described_class.call(archetype: archetype)

        expect(result[:custom_filters][:titles]).to include('Ruby on Rails Developer')
        expect(result[:custom_filters][:titles]).to include('Pleno')
        expect(result[:custom_filters][:locations]).to eq([ 'São Paulo, SP' ])
        expect(result[:custom_filters][:industries]).to eq([ 'Technology' ])
        expect(result[:custom_filters][:languages]).to eq([ 'Português', 'Inglês' ])
        expect(result[:custom_filters][:keywords]).to include('Ruby', 'Rails', 'PostgreSQL')
        expect(result[:custom_filters][:min_total_experience_years]).to eq(3)
      end

      it 'uses default balanced profile' do
        result = described_class.call(archetype: archetype)

        expect(result[:search_profile]).to eq('balanced')
        expect(result[:limit]).to eq(10)
      end
    end

    context 'with senior archetype' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Tech Lead',
          seniority: :lead,
          min_experience_years: 8
        )
      end

      it 'includes lead titles in filters' do
        result = described_class.call(archetype: archetype)

        expect(result[:custom_filters][:titles]).to include('Lead')
        expect(result[:custom_filters][:titles]).to include('Tech Lead')
        expect(result[:custom_filters][:titles]).to include('Líder Técnico')
      end

      it 'includes seniority in query' do
        result = described_class.call(archetype: archetype)

        expect(result[:query]).to include('Tech Lead level')
      end
    end

    context 'with work model preference' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Frontend Developer',
          work_model: :remote
        )
      end

      it 'includes work model in query' do
        result = described_class.call(archetype: archetype)

        expect(result[:query]).to include('preferring remote work')
      end
    end

    context 'with additional options' do
      let(:archetype) { create(:search_archetype, account: account, user: user) }

      let(:additional_options) do
        {
          limit: 50,
          offset: 20,
          show_emails: true,
          show_phone_numbers: true,
          require_emails: true,
          thread_id: 'thread-123',
          docid_blacklist: [ 'doc1', 'doc2' ]
        }
      end

      it 'merges additional options' do
        result = described_class.call(archetype: archetype, additional_options: additional_options)

        expect(result[:limit]).to eq(50)
        expect(result[:offset]).to eq(20)
        expect(result[:show_emails]).to be true
        expect(result[:show_phone_numbers]).to be true
        expect(result[:require_emails]).to be true
        expect(result[:thread_id]).to eq('thread-123')
        expect(result[:docid_blacklist]).to eq([ 'doc1', 'doc2' ])
      end
    end

    context 'with custom profile' do
      let(:archetype) { create(:search_archetype, account: account, user: user) }

      it 'uses fast profile settings' do
        result = described_class.call(archetype: archetype, profile: 'fast')

        expect(result[:search_profile]).to eq('fast')
        expect(result[:limit]).to eq(10)
      end

      it 'uses premium profile settings' do
        result = described_class.call(archetype: archetype, profile: 'premium')

        expect(result[:search_profile]).to eq('premium')
        expect(result[:limit]).to eq(10)
      end
    end

    context 'with global_filters in archetype' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Developer',
          global_filters: {
            'keywords' => [ 'agile', 'scrum', 'ci/cd' ],
            'companies' => [ 'Google', 'Meta' ],
            'universities' => [ 'Stanford', 'MIT' ]
          }
        )
      end

      it 'merges existing global_filters' do
        result = described_class.call(archetype: archetype)

        expect(result[:custom_filters][:keywords]).to include('agile', 'scrum', 'ci/cd')
        expect(result[:custom_filters][:companies]).to eq([ 'Google', 'Meta' ])
        expect(result[:custom_filters][:universities]).to eq([ 'Stanford', 'MIT' ])
      end

      it 'includes keywords in query' do
        result = described_class.call(archetype: archetype)

        expect(result[:query]).to include('agile')
        expect(result[:query]).to include('scrum')
        expect(result[:query]).to include('ci/cd')
      end
    end

    context 'with minimal archetype data' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Software Engineer',
          seniority: nil,
          min_experience_years: nil,
          skills: [],
          languages: [],
          location: nil,
          industry: nil,
          work_model: nil,
          contract_type: nil,
          global_filters: nil
        )
      end

      it 'builds simple query' do
        result = described_class.call(archetype: archetype)

        expect(result[:query]).to eq('Software Engineer')
        expect(result[:custom_filters][:titles]).to eq([ 'Software Engineer' ])
      end

      it 'does not include empty filters' do
        result = described_class.call(archetype: archetype)

        expect(result[:custom_filters]).not_to have_key(:languages)
        expect(result[:custom_filters]).not_to have_key(:keywords)
        expect(result[:custom_filters]).not_to have_key(:min_total_experience_years)
        expect(result[:custom_filters]).not_to have_key(:locations)
        expect(result[:custom_filters]).not_to have_key(:industries)
      end
    end

    context 'with c_level seniority' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Chief Technology Officer',
          seniority: :c_level
        )
      end

      it 'includes executive titles' do
        result = described_class.call(archetype: archetype)

        expect(result[:custom_filters][:titles]).to include('CTO')
        expect(result[:custom_filters][:titles]).to include('Chief')
        expect(result[:custom_filters][:titles]).to include('VP')
      end
    end

    context 'with multiple job titles in query' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Software Engineer, Backend Developer, API Architect'
        )
      end

      it 'extracts multiple titles' do
        result = described_class.call(archetype: archetype)

        expect(result[:custom_filters][:titles]).to include('Software Engineer')
        expect(result[:custom_filters][:titles]).to include('Backend Developer')
        expect(result[:custom_filters][:titles]).to include('API Architect')
      end

      it 'limits to first 3 titles from query' do
        archetype.update(query: 'Title1, Title2, Title3, Title4, Title5')
        result = described_class.call(archetype: archetype)

        titles_from_query = result[:custom_filters][:titles].select { |t| t.start_with?('Title') }
        expect(titles_from_query.size).to eq(3)
      end
    end
  end
end
