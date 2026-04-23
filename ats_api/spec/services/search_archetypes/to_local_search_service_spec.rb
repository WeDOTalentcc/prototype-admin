require 'rails_helper'

RSpec.describe SearchArchetypes::ToLocalSearchService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe '.call' do
    context 'with complete archetype' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Ruby on Rails Developer',
          seniority: 'senior',
          min_experience_years: 5,
          skills: [ 'Ruby', 'Rails', 'PostgreSQL' ],
          languages: [ 'Português', 'Inglês' ],
          location: 'São Paulo, SP',
          industry: 'Tecnologia',
          work_model: 'remote',
          contract_type: 'clt'
        )
      end

      it 'builds complete search text' do
        result = described_class.call(archetype: archetype)

        expect(result[:search_text]).to include('Ruby on Rails Developer')
        expect(result[:search_text]).to include('sênior')
        expect(result[:search_text]).to include('5+ anos de experiência')
        expect(result[:search_text]).to include('São Paulo, SP')
        expect(result[:search_text]).to include('Tecnologia')
        expect(result[:search_text]).to include('remoto')
        expect(result[:search_text]).to include('CLT')
      end

      it 'builds where filters hash' do
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters]).to include(
          is_deleted: false,
          position_level: { in: [ 'Sênior', 'Senior' ] },
          years_of_experience_range: { gte: 5 },
          city: { ilike: '%São Paulo%' },
          state: { ilike: '%SP%' },
          remote_work: true,
          clt_expectation: { not: nil },
          skills: { in: [ 'ruby', 'rails', 'postgresql' ] },
          languages: { in: [ 'português', 'inglês' ] }
        )
      end

      it 'suggests hybrid search for detailed queries' do
        result = described_class.call(archetype: archetype)

        expect(result[:use_hybrid]).to be true
      end

      it 'returns default limit' do
        result = described_class.call(archetype: archetype)

        expect(result[:limit]).to eq(50)
      end
    end

    context 'with minimal archetype' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Developer',
          seniority: nil,
          min_experience_years: nil,
          skills: [],
          languages: [],
          location: nil,
          industry: nil,
          work_model: 'any_work_model',
          contract_type: 'any_contract',
          local_filters: nil,
          global_filters: nil
        )
      end

      it 'builds simple search text' do
        result = described_class.call(archetype: archetype)

        expect(result[:search_text]).to eq('Developer')
      end

      it 'builds minimal filters' do
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters]).to eq({ is_deleted: false })
      end

      it 'does not suggest hybrid for short queries' do
        result = described_class.call(archetype: archetype)

        expect(result[:use_hybrid]).to be false
      end
    end

    context 'with seniority levels' do
      it 'maps intern to correct position levels' do
        archetype = create(:search_archetype, :intern, account: account, user: user)
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:position_level][:in]).to include('Estágio', 'Trainee')
      end

      it 'maps c_level to executive positions' do
        archetype = create(:search_archetype, :c_level, account: account, user: user)
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:position_level][:in]).to include('VP', 'CTO', 'CEO')
      end
    end

    context 'with work model preferences' do
      it 'filters for remote work' do
        archetype = create(:search_archetype, :remote, account: account, user: user)
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:remote_work]).to be true
      end

      it 'filters for onsite work' do
        archetype = create(:search_archetype, :onsite, account: account, user: user)
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:remote_work]).to be false
      end

      it 'filters for hybrid work' do
        archetype = create(:search_archetype, :hybrid, account: account, user: user)
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:mobility][:ilike]).to include('híbrido')
      end
    end

    context 'with contract type preferences' do
      it 'filters for CLT' do
        archetype = create(:search_archetype, :clt, account: account, user: user)
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:clt_expectation]).to eq({ not: nil })
      end

      it 'filters for PJ' do
        archetype = create(:search_archetype, :pj, account: account, user: user)
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:pj_expectation]).to eq({ not: nil })
      end
    end

    context 'with additional options' do
      let(:archetype) { create(:search_archetype, account: account, user: user) }

      it 'accepts custom limit' do
        result = described_class.call(
          archetype: archetype,
          additional_options: { limit: 100 }
        )

        expect(result[:limit]).to eq(100)
      end

      it 'clamps limit to maximum' do
        result = described_class.call(
          archetype: archetype,
          additional_options: { limit: 500 }
        )

        expect(result[:limit]).to eq(200)
      end

      it 'clamps limit to minimum' do
        result = described_class.call(
          archetype: archetype,
          additional_options: { limit: 0 }
        )

        expect(result[:limit]).to eq(1)
      end

      it 'accepts custom max_pages' do
        result = described_class.call(
          archetype: archetype,
          additional_options: { max_pages: 5 }
        )

        expect(result[:max_pages]).to eq(5)
      end

      it 'accepts custom order' do
        custom_order = { created_at: :asc }
        result = described_class.call(
          archetype: archetype,
          additional_options: { order: custom_order }
        )

        expect(JSON.parse(result[:order_json])).to eq({ 'created_at' => 'asc' })
      end

      it 'forces hybrid search mode' do
        result = described_class.call(
          archetype: archetype,
          additional_options: { use_hybrid: true }
        )

        expect(result[:use_hybrid]).to be true
      end
    end

    context 'with custom local_filters' do
      let(:archetype) do
        create(:search_archetype,
          account: account,
          user: user,
          query: 'Developer',
          local_filters: {
            'keywords' => [ 'react', 'nodejs' ],
            'where' => { 'age_range' => { 'gte' => 25 } },
            'filter' => { 'education_levels' => [ 'Superior Completo' ] },
            'limit' => 75,
            'max_pages' => 3
          }
        )
      end

      it 'merges keywords into search text' do
        result = described_class.call(archetype: archetype)

        expect(result[:search_text]).to include('react')
        expect(result[:search_text]).to include('nodejs')
      end

      it 'merges custom where filters' do
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:age_range]).to eq({ gte: 25 })
      end

      it 'includes custom filter in filter_json' do
        result = described_class.call(archetype: archetype)

        filters = JSON.parse(result[:filter_json])
        expect(filters['education_levels']).to eq([ 'Superior Completo' ])
      end

      it 'uses custom limit from local_filters' do
        result = described_class.call(archetype: archetype)

        expect(result[:limit]).to eq(75)
      end

      it 'uses custom max_pages from local_filters' do
        result = described_class.call(archetype: archetype)

        expect(result[:max_pages]).to eq(3)
      end
    end

    context 'with location parsing' do
      it 'extracts city and state from location' do
        archetype = create(:search_archetype,
          account: account,
          user: user,
          location: 'Rio de Janeiro, RJ'
        )
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:city][:ilike]).to eq('%Rio de Janeiro%')
        expect(result[:where_filters][:state][:ilike]).to eq('%RJ%')
      end

      it 'handles city-only location' do
        archetype = create(:search_archetype,
          account: account,
          user: user,
          location: 'São Paulo'
        )
        result = described_class.call(archetype: archetype)

        expect(result[:where_filters][:city][:ilike]).to eq('%São Paulo%')
        expect(result[:where_filters]).not_to have_key(:state)
      end
    end
  end
end
