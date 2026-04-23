# frozen_string_literal: true

require 'rails_helper'

RSpec.describe EntityColumn, type: :model do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe 'associations' do
    it { should belong_to(:user).optional }
    it { should belong_to(:account) }
    it { should belong_to(:shortlist).optional }
    it { should belong_to(:job).optional }
  end

  describe 'validations' do
    it { should validate_presence_of(:entity) }
    it { should validate_presence_of(:requested) }

    context 'when is_views is true' do
      subject { build(:entity_column, is_views: true, account: account) }
      it { should validate_presence_of(:label) }
    end

    context 'when is_views is false' do
      subject { build(:entity_column, is_views: false, account: account) }
      it { should_not validate_presence_of(:label) }
    end

    describe 'entity format validation' do
      let(:entity_column) { build(:entity_column, account: account) }

      it 'allows lowercase letters and underscores' do
        entity_column.entity = 'candidate_profile'
        expect(entity_column).to be_valid
      end

      it 'rejects uppercase letters' do
        entity_column.entity = 'Candidate'
        expect(entity_column).not_to be_valid
        expect(entity_column.errors[:entity]).to include('must contain only lowercase letters and underscores')
      end

      it 'rejects spaces' do
        entity_column.entity = 'candidate profile'
        expect(entity_column).not_to be_valid
      end

      it 'rejects special characters' do
        entity_column.entity = 'candidate-profile'
        expect(entity_column).not_to be_valid
      end
    end
  end

  describe 'scopes' do
    let!(:public_column) { create(:entity_column, is_public: true, account: account) }
    let!(:private_column) { create(:entity_column, is_public: false, user: user, account: account) }
    let!(:main_column) { create(:entity_column, is_main: true, is_views: false, account: account) }
    let!(:view_column) { create(:entity_column, is_views: true, account: account) }

    describe '.public_columns' do
      it 'returns only public columns' do
        expect(EntityColumn.public_columns).to include(public_column)
        expect(EntityColumn.public_columns).not_to include(private_column)
      end
    end

    describe '.private_for_user' do
      it 'returns private columns for specific user' do
        result = EntityColumn.private_for_user(user.id)
        expect(result).to include(private_column)
        expect(result).not_to include(public_column)
      end
    end

    describe '.accessible_by' do
      it 'returns both public and user private columns' do
        result = EntityColumn.accessible_by(user.id)
        expect(result).to include(public_column, private_column)
      end
    end

    describe '.main_columns' do
      it 'returns main columns only' do
        expect(EntityColumn.main_columns).to include(main_column)
        expect(EntityColumn.main_columns).not_to include(view_column)
      end
    end

    describe '.view_columns' do
      it 'returns view columns only' do
        expect(EntityColumn.view_columns).to include(view_column)
        expect(EntityColumn.view_columns).not_to include(main_column)
      end
    end

    describe '.by_entity' do
      it 'returns columns for specific entity' do
        candidate_column = create(:entity_column, entity: 'candidate', account: account)
        job_column = create(:entity_column, entity: 'job', account: account)

        result = EntityColumn.by_entity('candidates')
        expect(result).to include(candidate_column)
        expect(result).not_to include(job_column)
      end
    end

    describe '.by_requested' do
      it 'returns columns for specific requested type' do
        default_column = create(:entity_column, requested: 'default', account: account)
        shortlist_column = create(:entity_column, requested: 'shortlists', account: account)

        result = EntityColumn.by_requested('default')
        expect(result).to include(default_column)
        expect(result).not_to include(shortlist_column)
      end
    end
  end

  describe 'callbacks' do
    describe 'before_validation' do
      it 'normalizes entity name' do
        entity_column = build(:entity_column, entity: 'Candidates', account: account)
        entity_column.valid?
        expect(entity_column.entity).to eq('candidate')
      end
    end

    describe 'before_save merge_shortlist_columns' do
      let(:entity_column) do
        create(:entity_column,
               entity: 'candidate',
               requested: 'shortlists',
               columns_view: [],
               account: account
              )
      end

      let!(:report) do
        create(:report,
               name: 'Performance Report',
               is_deleted: false,
               is_main: true,
               account: account
              )
      end

      it 'merges shortlist columns on save for shortlist requesters' do
        entity_column.save
        entity_column.reload

        expect(entity_column.columns_view).to include(
          hash_including(
            'value' => 'performancereport',
            'text' => 'Performance report',
            'type' => 'ShortlistText'
          )
        )
      end
    end
  end

  describe 'search_data' do
    let(:entity_column) { create(:entity_column, account: account, user: user) }

    it 'returns correct search data structure' do
      search_data = entity_column.search_data

      expect(search_data).to include(
        :id, :entity, :user_id, :requested, :shortlist_id, :is_main,
        :label, :is_views, :is_public, :business_ids, :created_at, :account_id
      )
    end

    it 'joins business_ids with comma' do
      entity_column = create(:entity_column, business_ids: [ 1, 2, 3 ], account: account)
      expect(entity_column.search_data[:business_ids]).to eq('1,2,3')
    end
  end

  describe '.find_or_create_by_entity' do
    context 'when entity column exists' do
      let!(:existing_column) do
        create(:entity_column,
               entity: 'candidate',
               user: user,
               requested: 'default',
               account: account
              )
      end

      it 'returns existing column' do
        result = EntityColumn.find_or_create_by_entity(
          'candidates',
          user.id,
          requested: 'default',
          account_id: account.id
        )

        expect(result).to eq(existing_column)
      end
    end

    context 'when entity column does not exist' do
      it 'creates new column with default structure' do
        expect {
          EntityColumn.find_or_create_by_entity(
            'candidates',
            user.id,
            requested: 'default',
            account_id: account.id
          )
        }.to change(EntityColumn, :count).by(1)
      end

      it 'sets correct attributes' do
        column = EntityColumn.find_or_create_by_entity(
          'candidates',
          user.id,
          requested: 'shortlists',
          shortlist_id: 123,
          job_id: 456,
          account_id: account.id
        )

        expect(column.entity).to eq('candidate')
        expect(column.user_id).to eq(user.id)
        expect(column.requested).to eq('shortlists')
        expect(column.shortlist_id).to eq(123)
        expect(column.job_id).to eq(456)
        expect(column.is_main).to be true
        expect(column.is_views).to be false
      end
    end
  end

  describe '#available_columns' do
    let(:entity_column) { create(:entity_column, entity: 'candidate', account: account) }

    before do
      allow(EntityColumnService::Structure).to receive(:supported_entity?).with('candidate').and_return(true)
      allow(EntityColumnService::Structure).to receive(:entity_columns).and_return([
        { value: 'name', text: 'Name' },
        { value: 'email', text: 'Email' }
      ])
    end

    it 'returns available columns for supported entity' do
      result = entity_column.available_columns
      expect(result).to eq([
        { value: 'name', text: 'Name' },
        { value: 'email', text: 'Email' }
      ])
    end

    it 'returns empty array for unsupported entity' do
      allow(EntityColumnService::Structure).to receive(:supported_entity?).and_return(false)
      expect(entity_column.available_columns).to eq([])
    end
  end

  describe '#all_columns' do
    let(:entity_column) { create(:entity_column, entity: 'candidate', account: account) }

    before do
      allow(EntityColumnService::Structure).to receive(:supported_entity?).with('candidate').and_return(true)
      allow(EntityColumnService::Structure).to receive(:entity_columns).and_return([
        { value: 'name', text: 'Name' },
        { value: 'email', text: 'Email' },
        { value: 'phone', text: 'Phone' }
      ])
    end

    it 'returns all columns for supported entity' do
      result = entity_column.all_columns
      expect(result).to eq([
        { value: 'name', text: 'Name' },
        { value: 'email', text: 'Email' },
        { value: 'phone', text: 'Phone' }
      ])
    end
  end
end
