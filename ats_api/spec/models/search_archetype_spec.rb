require 'rails_helper'

RSpec.describe SearchArchetype, type: :model do
  subject { build(:search_archetype) }

  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:user).optional }
    it { should have_many(:sourcings).dependent(:nullify) }
  end

  describe 'validations' do
    it { should validate_presence_of(:name) }

    it 'validates uniqueness of uid' do
      existing = create(:search_archetype)
      new_archetype = build(:search_archetype, uid: existing.uid)
      expect(new_archetype).not_to be_valid
      expect(new_archetype.errors[:uid]).to include('has already been taken')
    end
  end

  describe 'enums' do
    it { should define_enum_for(:seniority).with_values(
      intern: 0, junior: 1, mid: 2, senior: 3,
      lead: 4, manager: 5, director: 6, c_level: 7
    ).with_prefix(true) }

    it { should define_enum_for(:work_model).with_values(
      any_work_model: 0, remote: 1, hybrid: 2, onsite: 3
    ).with_prefix(true) }

    it { should define_enum_for(:contract_type).with_values(
      any_contract: 0, clt: 1, pj: 2, freelance: 3
    ).with_prefix(true) }
  end

  describe 'callbacks' do
    describe 'before_validation :generate_uid' do
      it 'generates uid on create' do
        archetype = build(:search_archetype, uid: nil)
        expect(archetype.uid).to be_nil
        archetype.validate
        expect(archetype.uid).to be_present
        expect(archetype.uid).to match(/\A[0-9a-f-]{36}\z/)
      end

      it 'does not override existing uid' do
        original_uid = SecureRandom.uuid
        archetype = build(:search_archetype, uid: original_uid)
        archetype.validate
        expect(archetype.uid).to eq(original_uid)
      end
    end

    describe 'before_save :normalize_arrays' do
      it 'normalizes skills array' do
        archetype = create(:search_archetype, skills: [ '  Python  ', 'Ruby', '', '  Java', 'Python' ])
        expect(archetype.skills).to eq([ 'Python', 'Ruby', 'Java' ])
      end

      it 'normalizes tags array' do
        archetype = create(:search_archetype, tags: [ 'backend  ', '  ', 'frontend', 'backend' ])
        expect(archetype.tags).to eq([ 'backend', 'frontend' ])
      end

      it 'normalizes languages array' do
        archetype = create(:search_archetype, languages: [ 'Português', '', 'Inglês  ', 'Português' ])
        expect(archetype.languages).to eq([ 'Português', 'Inglês' ])
      end

      it 'handles nil arrays' do
        archetype = create(:search_archetype, skills: nil, tags: nil, languages: nil)
        expect(archetype.skills).to eq([])
        expect(archetype.tags).to eq([])
        expect(archetype.languages).to eq([])
      end
    end
  end

  describe 'scopes' do
    describe '.active' do
      let!(:active_archetypes) { create_list(:search_archetype, 3) }
      let!(:deleted_archetypes) { create_list(:search_archetype, 2, :deleted) }

      it 'returns only non-deleted archetypes' do
        expect(SearchArchetype.active).to match_array(active_archetypes)
      end
    end
  end

  describe '#seniority_label' do
    it 'returns localized label for intern' do
      archetype = build(:search_archetype, seniority: :intern)
      expect(archetype.seniority_label).to eq('Estágio')
    end

    it 'returns localized label for junior' do
      archetype = build(:search_archetype, seniority: :junior)
      expect(archetype.seniority_label).to eq('Júnior')
    end

    it 'returns localized label for lead' do
      archetype = build(:search_archetype, seniority: :lead)
      expect(archetype.seniority_label).to eq('Tech Lead')
    end

    it 'returns humanized value for nil' do
      archetype = build(:search_archetype, seniority: nil)
      expect(archetype.seniority_label).to be_nil
    end
  end

  describe '#work_model_label' do
    it 'returns localized label for remote' do
      archetype = build(:search_archetype, work_model: :remote)
      expect(archetype.work_model_label).to eq('Remoto')
    end

    it 'returns localized label for hybrid' do
      archetype = build(:search_archetype, work_model: :hybrid)
      expect(archetype.work_model_label).to eq('Híbrido')
    end

    it 'returns localized label for any' do
      archetype = build(:search_archetype, work_model: :any_work_model)
      expect(archetype.work_model_label).to eq('Qualquer')
    end
  end

  describe '#contract_type_label' do
    it 'returns localized label for clt' do
      archetype = build(:search_archetype, contract_type: :clt)
      expect(archetype.contract_type_label).to eq('CLT')
    end

    it 'returns localized label for pj' do
      archetype = build(:search_archetype, contract_type: :pj)
      expect(archetype.contract_type_label).to eq('PJ')
    end
  end

  describe '#filters_for' do
    let(:archetype) { create(:search_archetype, :tech_lead_python) }

    context 'with local source' do
      it 'returns local filters with structured data' do
        filters = archetype.filters_for(:local)

        expect(filters).to include(:skills, :position_level, :languages)
        expect(filters[:skills]).to eq([ 'Python', 'Django', 'AWS', 'Docker', 'PostgreSQL' ])
        expect(filters[:position_level]).to eq('lead')
        expect(filters[:languages]).to eq([ 'Português', 'Inglês' ])
      end

      it 'includes remote_work when work_model is remote' do
        archetype.update(work_model: :remote)
        filters = archetype.filters_for(:local)
        expect(filters[:remote_work]).to eq(true)
      end

      it 'extracts city and state from location' do
        archetype.update(location: 'São Paulo, SP')
        filters = archetype.filters_for(:local)
        expect(filters[:city]).to eq('São Paulo')
        expect(filters[:state]).to eq('SP')
      end

      it 'merges with local_filters json' do
        archetype.update(local_filters: { keywords: 'python django', role_name: 'Tech Lead' })
        filters = archetype.filters_for(:local)
        expect(filters[:keywords]).to eq('python django')
        expect(filters[:role_name]).to eq('Tech Lead')
      end
    end

    context 'with global source' do
      it 'returns global filters with structured data' do
        filters = archetype.filters_for(:global)

        expect(filters).to include(:skills, :languages)
        expect(filters[:years_experience]).to eq(8)
        expect(filters[:skills]).to eq([ 'Python', 'Django', 'AWS', 'Docker', 'PostgreSQL' ])
      end

      it 'extracts titles from query' do
        archetype.update(query: 'Tech Lead, Senior Developer, Python Specialist')
        filters = archetype.filters_for(:global)
        expect(filters[:current_or_past_titles]).to eq([ 'Tech Lead', 'Senior Developer', 'Python Specialist' ])
      end

      it 'limits titles to first 3' do
        archetype.update(query: 'Title 1, Title 2, Title 3, Title 4, Title 5')
        filters = archetype.filters_for(:global)
        expect(filters[:current_or_past_titles].size).to eq(3)
      end

      it 'includes location as array' do
        archetype.update(location: 'São Paulo, SP')
        filters = archetype.filters_for(:global)
        expect(filters[:locations]).to eq([ 'São Paulo, SP' ])
      end
    end

    context 'with invalid source' do
      it 'returns only query for unknown source' do
        filters = archetype.filters_for(:invalid)
        expect(filters).to eq({ query: archetype.query })
      end
    end
  end

  describe '#execute_search!' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:archetype) { create(:search_archetype, account: account, user: user) }
    let(:mock_sourcing) { double(id: 123, uid: 'test-uid', status: 'processing') }

    before do
      allow_any_instance_of(SearchArchetypes::ExecuteSearchService).to receive(:call).and_return(mock_sourcing)
    end

    it 'increments usage_count' do
      expect {
        archetype.execute_search!(user: user, sources: [ 'local' ])
      }.to change { archetype.reload.usage_count }.by(1)
    end

    it 'updates last_used_at' do
      expect(archetype.last_used_at).to be_nil
      archetype.execute_search!(user: user, sources: [ 'local' ])
      expect(archetype.reload.last_used_at).to be_present
      expect(archetype.last_used_at).to be_within(1.second).of(Time.current)
    end

    it 'calls ExecuteSearchService' do
      service = instance_double(SearchArchetypes::ExecuteSearchService)
      allow(SearchArchetypes::ExecuteSearchService).to receive(:new).with(
        archetype: archetype,
        user: user,
        sources: [ 'local' ]
      ).and_return(service)
      expect(service).to receive(:call).and_return(mock_sourcing)

      archetype.execute_search!(user: user, sources: [ 'local' ])
    end

    it 'accepts multiple sources' do
      service = instance_double(SearchArchetypes::ExecuteSearchService)
      allow(SearchArchetypes::ExecuteSearchService).to receive(:new).with(
        archetype: archetype,
        user: user,
        sources: [ 'local', 'global' ]
      ).and_return(service)
      expect(service).to receive(:call).and_return(mock_sourcing)

      archetype.execute_search!(user: user, sources: [ 'local', 'global' ])
    end
  end

  describe '#duplicate_for' do
    let(:original_user) { create(:user) }
    let(:new_user) { create(:user) }
    let(:archetype) { create(:search_archetype, :with_usage, :public_archetype, user: original_user, name: 'Original') }

    it 'creates a duplicate with new user' do
      duplicate = archetype.duplicate_for(new_user)

      expect(duplicate.user).to eq(new_user)
      expect(duplicate.name).to eq('Original (cópia)')
    end

    it 'resets uid' do
      duplicate = archetype.duplicate_for(new_user)
      expect(duplicate.uid).to be_nil
    end

    it 'resets flags' do
      duplicate = archetype.duplicate_for(new_user)

      expect(duplicate.is_default).to eq(false)
      expect(duplicate.is_public).to eq(false)
    end

    it 'resets usage statistics' do
      duplicate = archetype.duplicate_for(new_user)

      expect(duplicate.usage_count).to eq(0)
      expect(duplicate.last_used_at).to be_nil
    end

    it 'copies attributes' do
      duplicate = archetype.duplicate_for(new_user)

      expect(duplicate.description).to eq(archetype.description)
      expect(duplicate.query).to eq(archetype.query)
      expect(duplicate.skills).to eq(archetype.skills)
      expect(duplicate.seniority).to eq(archetype.seniority)
    end

    it 'is not persisted' do
      duplicate = archetype.duplicate_for(new_user)
      expect(duplicate).not_to be_persisted
    end
  end

  describe '#search_data' do
    let(:archetype) { create(:search_archetype, :tech_lead_python) }

    it 'includes all required fields for indexing' do
      data = archetype.search_data

      expect(data).to include(
        :id, :uid, :name, :description, :query, :emoji,
        :seniority, :seniority_text, :work_model, :work_model_text,
        :contract_type, :contract_type_text, :min_experience_years,
        :industry, :location, :skills, :tags, :languages,
        :is_default, :is_public, :is_deleted, :usage_count,
        :last_used_at, :account_id, :user_id, :created_at, :updated_at
      )
    end

    it 'normalizes text fields to lowercase' do
      data = archetype.search_data
      expect(data[:name]).to eq(archetype.name.downcase)
      expect(data[:description]).to eq(archetype.description.downcase)
    end

    it 'includes enum labels' do
      data = archetype.search_data
      expect(data[:seniority_text]).to eq('Tech Lead')
      expect(data[:work_model_text]).to eq('Remoto')
    end

    it 'normalizes arrays to lowercase' do
      data = archetype.search_data
      expect(data[:skills]).to all(match(/\A[a-z0-9]+\z/))
    end
  end

  describe '.agg_search_array' do
    it 'returns aggregator configuration' do
      aggs = SearchArchetype.agg_search_array

      expect(aggs).to include(
        :seniority, :seniority_text, :work_model, :work_model_text,
        :contract_type, :contract_type_text, :industry, :skills,
        :tags, :languages, :is_default, :is_public, :user_id
      )
    end

    it 'has correct limits for each aggregator' do
      aggs = SearchArchetype.agg_search_array

      expect(aggs[:skills][:limit]).to eq(100)
      expect(aggs[:tags][:limit]).to eq(50)
      expect(aggs[:industry][:limit]).to eq(30)
    end
  end

  describe 'factory' do
    it 'has a valid default factory' do
      expect(subject).to be_valid
    end

    it 'creates valid default archetype' do
      archetype = build(:search_archetype, :default)
      expect(archetype).to be_valid
      expect(archetype.is_default).to eq(true)
      expect(archetype.is_public).to eq(true)
      expect(archetype.user).to be_nil
    end

    it 'creates valid tech_lead_python archetype' do
      archetype = build(:search_archetype, :tech_lead_python)
      expect(archetype).to be_valid
      expect(archetype.seniority).to eq('lead')
      expect(archetype.skills).to include('Python', 'Django', 'AWS')
    end
  end
end
