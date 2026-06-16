require 'rails_helper'

RSpec.describe ListRelationship, type: :model do
  describe 'associations' do
    it { is_expected.to belong_to(:list) }
    it { is_expected.to belong_to(:account) }
    it { is_expected.to belong_to(:reference) }
  end

  describe 'validations' do
    it { is_expected.to validate_presence_of(:reference_id) }
    it { is_expected.to validate_presence_of(:reference_type) }
    it { is_expected.to validate_presence_of(:list_id) }
    it { is_expected.to validate_presence_of(:account_id) }

    context 'when preventing duplicates' do
      let(:list) { create(:list) }
      let(:candidate) { create(:candidate, account: list.account) }

      it 'prevents duplicate relationships' do
        create(:list_relationship, list: list, reference: candidate, account: list.account)

        duplicate = build(:list_relationship, list: list, reference: candidate, account: list.account)
        expect(duplicate).not_to be_valid
        expect(duplicate.errors[:base]).to include('This relationship already exists in the list')
      end

      it 'allows relationship after deletion' do
        relationship = create(:list_relationship, list: list, reference: candidate, account: list.account)
        relationship.update(is_deleted: true)

        new_relationship = build(:list_relationship, list: list, reference: candidate, account: list.account)
        expect(new_relationship).to be_valid
      end
    end
  end

  describe 'scopes' do
    let!(:active_relationship) { create(:list_relationship) }
    let!(:deleted_relationship) { create(:list_relationship, :deleted) }

    it 'filters active relationships' do
      expect(described_class.active).to include(active_relationship)
      expect(described_class.active).not_to include(deleted_relationship)
    end

    it 'filters by reference type' do
      job_relationship = create(:list_relationship, :with_job)
      expect(described_class.by_reference_type('Job')).to include(job_relationship)
      expect(described_class.by_reference_type('Candidate')).not_to include(job_relationship)
    end
  end

  describe '#reindex_entity' do
    let(:list_relationship) { create(:list_relationship) }

    it 'reindexes the referenced entity' do
      expect(list_relationship.reference).to receive(:reindex)
      list_relationship.reindex_entity
    end

    it 'handles errors gracefully' do
      allow(list_relationship).to receive(:reference).and_return(nil)
      expect { list_relationship.reindex_entity }.not_to raise_error
    end
  end

  describe '#update_list_counts' do
    let(:list) { create(:list) }
    let(:candidate) { create(:candidate, account: list.account) }

    it 'updates list counts after creation' do
      expect(list).to receive(:count_relationships)
      create(:list_relationship, list: list, reference: candidate, account: list.account)
    end

    it 'updates list counts after deletion' do
      relationship = create(:list_relationship, list: list, reference: candidate, account: list.account)
      expect(list).to receive(:count_relationships)
      relationship.destroy
    end
  end

  describe 'search_data' do
    let(:list_relationship) { create(:list_relationship) }

    it 'includes default fields' do
      data = list_relationship.search_data
      expect(data).to include(:id, :list_id, :reference_type, :reference_id)
      expect(data).to include(:position, :account_id)
    end

    it 'merges reference search data' do
      allow(list_relationship.reference).to receive(:search_data).and_return({ name: 'Test' })
      data = list_relationship.search_data
      expect(data).to include(:name)
    end
  end
end
