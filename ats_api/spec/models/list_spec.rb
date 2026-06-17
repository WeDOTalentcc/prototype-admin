require 'rails_helper'

RSpec.describe List, type: :model do
  describe 'associations' do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to belong_to(:account) }
    it { is_expected.to have_many(:list_relationships).dependent(:destroy) }
  end

  describe 'validations' do
    it { is_expected.to validate_presence_of(:name) }
    it { is_expected.to validate_presence_of(:user_id) }
    it { is_expected.to validate_presence_of(:account_id) }
  end

  describe '#count_relationships' do
    let(:list) { create(:list) }
    let(:candidate1) { create(:candidate, account: list.account) }
    let(:candidate2) { create(:candidate, account: list.account) }
    let(:job) { create(:job, account: list.account) }

    before do
      create(:list_relationship, list: list, reference: candidate1, account: list.account)
      create(:list_relationship, list: list, reference: candidate2, account: list.account)
      create(:list_relationship, list: list, reference: job, account: list.account)
    end

    it 'counts relationships correctly' do
      list.count_relationships
      expect(list.candidates_count).to eq(2)
      expect(list.jobs_count).to eq(1)
    end

    it 'excludes deleted relationships' do
      list.list_relationships.first.update(is_deleted: true)
      list.count_relationships
      expect(list.candidates_count).to eq(1)
    end
  end

  describe '.count_all_relationships' do
    let!(:list1) { create(:list, :with_candidates) }
    let!(:list2) { create(:list, :with_jobs) }

    it 'recalculates counts for all lists' do
      expect { described_class.count_all_relationships }.not_to raise_error
    end
  end

  describe 'search_data' do
    let(:list) { create(:list) }

    it 'includes all required fields' do
      data = list.search_data
      expect(data).to include(:id, :name, :user_name, :account_id)
      expect(data).to include(:candidates_count, :jobs_count)
    end
  end
end
