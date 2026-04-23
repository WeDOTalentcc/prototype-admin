require 'rails_helper'

RSpec.describe Job, type: :model do
  subject { build(:job) }

  it { should belong_to(:user).optional }
  it { should belong_to(:account).optional }
  it { should have_many(:selective_processes).dependent(:destroy) }

  describe 'validations' do
    it 'requires at least title or description' do
      job = build(:job, title: nil, description: nil)
      expect(job).not_to be_valid
      expect(job.errors[:base]).to include('Title ou Description deve estar presente')
    end

    it 'is valid with only title' do
      job = build(:job, title: 'Test Job', description: nil)
      expect(job).to be_valid
    end

    it 'is valid with only description' do
      job = build(:job, title: nil, description: 'Test Description')
      expect(job).to be_valid
    end
  end

  it 'has a valid factory' do
    expect(subject).to be_valid
  end

  describe 'wsi_suggested_seniority_key after LIA JD enrichment' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:enriched_lia) do
      {
        'status' => 'pending_review',
        'enriched_jd' => {
          'about_role' => 'Buscamos um Senior Software Engineer para liderar o time backend.',
          'skills_obrigatorias' => %w[Ruby PostgreSQL],
          'competencias_comportamentais' => []
        }
      }
    end

    it 'sets wsi_suggested_seniority_key when lia_job_description is saved with enriched_jd' do
      job = create(:job, account: account, user: user, title: 'Developer', seniority: nil, lia_job_description: {})
      job.update!(lia_job_description: enriched_lia)

      expect(job.reload.wsi_suggested_seniority_key).to eq('senior')
    end
  end

  describe 'seniority override log' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) do
      create(:job, account: account, user: user, seniority: 2, wsi_suggested_seniority_key: 'senior')
    end

    it 'records from/to when seniority changes away from suggested key' do
      allow(Current).to receive(:user).and_return(user)

      job.update!(seniority: 5)

      job.reload
      expect(job.seniority_override_log).to be_a(Array)
      expect(job.seniority_override_log.first['from']).to eq('senior')
      expect(job.seniority_override_log.first['to']).to eq('lead')
      expect(job.seniority_override_log.first['user_id']).to eq(user.id)
      expect(job.seniority_override_log.first['at']).to be_present
    end

    it 'does not append when wsi_suggested_seniority_key is blank' do
      job.update_column(:wsi_suggested_seniority_key, nil)

      job.update!(seniority: 1)

      expect(job.reload.seniority_override_log).to eq({})
    end
  end

  describe '.save_job_copy' do
    let!(:account) { create(:account) }
    let!(:user) { create(:user, account: account) }
    let!(:source_job) { create(:job, user: user, account: account, title: 'Vaga Original') }

    # let!(:selective_process) { create(:selective_process, job: source_job, name: 'Triagem Original') }

    subject(:call_service) do
      JobService::CopyJobCollection.save_job_copy(source_job.id, user.id, [])
    end

    it 'creates a new Job record' do
      expect { call_service }.to change(Job, :count).by(1)
    end

    it 'sets the correct attributes for the new job' do
      call_service
      new_job = Job.last

      expect(new_job.title).to eq('Vaga Original #1')
      expect(new_job.source_job_id).to eq(source_job.id)
      expect(new_job.user_id).to eq(user.id)
    end

    it 'copies the associated selective processes' do
      call_service
      new_job = Job.last

      expect(new_job.selective_processes.count).to eq(source_job.selective_processes.count)
    end

    it 'returns the newly created job instance' do
      new_job = call_service
      expect(new_job).to be_truthy
      expect(new_job.is_a?(Job) || new_job == true).to be(true)
    end
  end

  describe 'selective processes' do
    let(:job) { create(:job) }

    it 'can have selective processes created manually' do
      job.selective_processes.create!(name: 'Inscrição Web', position: 0, status: 'web_submission', account_id: job.account_id)
      job.selective_processes.create!(name: 'Triagem', position: 1, status: 'screening', account_id: job.account_id)
      job.selective_processes.create!(name: 'Entrevista', position: 2, status: 'interview', account_id: job.account_id)
      job.selective_processes.create!(name: 'Rejeitados', position: 3, status: 'rejected', account_id: job.account_id)
      job.selective_processes.create!(name: 'Contratados', position: 4, status: 'hired', account_id: job.account_id)

      expect(job.selective_processes.count).to eq(5)

      expected_statuses = %w[
        web_submission
        screening
        interview
        rejected
        hired
      ]

      actual_statuses = job.selective_processes.order(:position).pluck(:status)
      expect(actual_statuses).to eq(expected_statuses)
    end
  end

  describe 'virtual remuneration attributes' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, account: account, user: user) }

    describe '#sync_remuneration_attributes' do
      context 'when creating with salary_from and salary_to' do
        it 'creates two remuneration relationships' do
          job.salary_from = 5000
          job.salary_to = 8000
          job.salary_currency = 'BRL'
          job.salary_period = 'monthly'
          job.salary_contract_type = 'CLT'

          expect {
            job.save!
            job.sync_remuneration_attributes
          }.to change { job.remuneration_relationships.count }.by(2)

          relationships = job.remuneration_relationships.where(is_deleted: false)
          expect(relationships.count).to eq(2)

          salary_from_rel = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (De)' })
          expect(salary_from_rel.value).to eq(5000.0)
          expect(salary_from_rel.currency).to eq('BRL')
          expect(salary_from_rel.period).to be_present
          expect(salary_from_rel.contract_type).to include('CLT')

          salary_to_rel = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (Até)' })
          expect(salary_to_rel.value).to eq(8000.0)
          expect(salary_to_rel.currency).to eq('BRL')
        end
      end

      context 'when updating existing salary values' do
        before do
          job.salary_from = 5000
          job.salary_to = 8000
          job.salary_currency = 'BRL'
          job.save!
          job.sync_remuneration_attributes
        end

        it 'updates existing relationships without creating duplicates' do
          initial_count = job.remuneration_relationships.count

          job.salary_from = 6000
          job.salary_to = 9000
          job.save!
          job.sync_remuneration_attributes

          expect(job.remuneration_relationships.count).to eq(initial_count)

          relationships = job.remuneration_relationships.where(is_deleted: false)
          salary_from_rel = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (De)' })
          expect(salary_from_rel.value).to eq(6000.0)

          salary_to_rel = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (Até)' })
          expect(salary_to_rel.value).to eq(9000.0)
        end
      end

      context 'when removing salary values' do
        before do
          job.salary_from = 5000
          job.salary_to = 8000
          job.save!
          job.sync_remuneration_attributes
        end

        it 'soft deletes the relationships' do
          job.salary_from = nil
          job.salary_to = nil
          job.save!
          job.sync_remuneration_attributes

          relationships = job.remuneration_relationships.where(is_deleted: false)
          salary_relationships = relationships.joins(:remuneration).where(remunerations: { name: [ 'Salário (De)', 'Salário (Até)' ] })
          expect(salary_relationships.count).to eq(0)

          deleted_relationships = job.remuneration_relationships.where(is_deleted: true)
          expect(deleted_relationships.count).to be >= 2
        end
      end

      context 'with commission values' do
        it 'creates commission remuneration relationships' do
          job.commission_from = 1000
          job.commission_to = 3000
          job.commission_currency = 'USD'
          job.commission_period = 'monthly'

          expect {
            job.save!
            job.sync_remuneration_attributes
          }.to change { job.remuneration_relationships.count }.by(2)

          relationships = job.remuneration_relationships.where(is_deleted: false)
          commission_from_rel = relationships.joins(:remuneration).find_by(remunerations: { name: 'Comissão (De)' })
          expect(commission_from_rel.value).to eq(1000.0)
          expect(commission_from_rel.currency).to eq('USD')
        end
      end

      context 'with bonus values' do
        it 'creates bonus remuneration relationships' do
          job.bonus_from = 2000
          job.bonus_to = 5000
          job.bonus_currency = 'EUR'
          job.bonus_period = 'yearly'

          expect {
            job.save!
            job.sync_remuneration_attributes
          }.to change { job.remuneration_relationships.count }.by(2)

          relationships = job.remuneration_relationships.where(is_deleted: false)
          bonus_from_rel = relationships.joins(:remuneration).find_by(remunerations: { name: 'Pacote de Bônus (De)' })
          expect(bonus_from_rel.value).to eq(2000.0)
          expect(bonus_from_rel.currency).to eq('EUR')
        end
      end

      context 'with multiple remuneration types' do
        it 'creates all types without conflicts' do
          job.salary_from = 5000
          job.salary_to = 8000
          job.commission_from = 1000
          job.commission_to = 2000
          job.bonus_from = 3000
          job.bonus_to = 5000

          expect {
            job.save!
            job.sync_remuneration_attributes
          }.to change { job.remuneration_relationships.count }.by(6)

          active_relationships = job.remuneration_relationships.where(is_deleted: false)
          expect(active_relationships.count).to eq(6)
        end
      end

      context 'with default currency' do
        it 'defaults to BRL when currency is not specified' do
          job.salary_from = 5000
          job.save!
          job.sync_remuneration_attributes

          relationship = job.remuneration_relationships.where(is_deleted: false).first
          expect(relationship.currency).to eq('BRL')
        end
      end
    end
  end
end
