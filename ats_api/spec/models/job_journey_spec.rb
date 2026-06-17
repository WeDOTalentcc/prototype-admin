# spec/models/job_journey_spec.rb
require 'rails_helper'

RSpec.describe JobJourney, type: :model do
  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:job).optional }
  end

  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_presence_of(:position) }
    it { should validate_numericality_of(:position).only_integer.is_greater_than_or_equal_to(0) }
  end

  describe 'scopes' do
    let(:account) { create(:account) }

    before do
      # Limpa os job_journeys criados automaticamente
      JobJourney.where(account_id: account.id).delete_all

      create(:job_journey, account: account, active: true, required: false, name: 'Active 1', position: 1)
      create(:job_journey, account: account, active: false, required: false, name: 'Inactive', position: 2)
      create(:job_journey, account: account, active: true, required: true, name: 'Required', position: 3)
      create(:job_journey, account: account, active: true, required: false, name: 'Optional', position: 4)
    end

    describe '.active' do
      it 'returns only active job journeys' do
        expect(JobJourney.where(account_id: account.id).active.count).to eq(3)
      end
    end

    describe '.required' do
      it 'returns only required job journeys' do
        expect(JobJourney.where(account_id: account.id).required.count).to eq(1)
      end
    end

    describe '.ordered' do
      it 'returns job journeys ordered by position' do
        journeys = JobJourney.where(account_id: account.id).ordered
        expect(journeys.first.name).to eq('Active 1')
        expect(journeys.last.name).to eq('Optional')
      end
    end
  end

  describe '.create_default_journeys_for_account' do
    let(:account) { create(:account) }

    before do
      # Limpa os job_journeys criados automaticamente pelo CreateTenantJob
      JobJourney.where(account_id: account.id).delete_all
    end

    it 'creates 15 default job journeys' do
      expect {
        JobJourney.create_default_journeys_for_account(account)
      }.to change { JobJourney.where(account_id: account.id).count }.by(15)
    end

    it 'creates journeys with correct attributes' do
      JobJourney.create_default_journeys_for_account(account)

      first_journey = JobJourney.find_by(position: 1, account_id: account.id)
      expect(first_journey.name).to eq('Informações Básicas')
      expect(first_journey.required).to be true
      expect(first_journey.active).to be true
    end

    it 'does not create duplicates' do
      JobJourney.create_default_journeys_for_account(account)
      initial_count = JobJourney.where(account_id: account.id).count

      JobJourney.create_default_journeys_for_account(account)

      expect(JobJourney.where(account_id: account.id).count).to eq(initial_count)
    end
  end
end
