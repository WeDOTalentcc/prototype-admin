require 'rails_helper'

RSpec.describe JobUser, type: :model do
  describe 'associations' do
    it { should belong_to(:user).optional }
    it { should belong_to(:job).optional }
    it { should belong_to(:account).optional }
  end

  describe 'validations' do
    it { should validate_presence_of(:user_id) }
    it { should validate_presence_of(:job_id) }
    it { should validate_numericality_of(:split).is_greater_than_or_equal_to(0).is_less_than_or_equal_to(100) }
  end

  describe 'factory' do
    it 'has a valid factory' do
      job_user = build(:job_user)
      expect(job_user).to be_valid
    end

    it 'creates job_user with hiring_manager trait' do
      job_user = create(:job_user, :hiring_manager)
      expect(job_user.person_function).to eq("Hiring Manager")
      expect(job_user.split).to eq(50.0)
    end
  end

  describe 'table_name' do
    it 'uses job_users table' do
      expect(JobUser.table_name).to eq('job_users')
    end
  end

  describe '.include_base' do
    let!(:account) { create(:account) }
    let!(:user) { create(:user, account: account) }
    let!(:job) { create(:job, account: account, user: user) }
    let!(:job_user) { create(:job_user, user: user, job: job, account: account) }

    it 'includes user and job data' do
      result = JobUser.include_base.find(job_user.id)

      expect(result).to be_present
      expect(result.user_name).to eq(user.name)
      expect(result.user_email).to eq(user.email)
      expect(result.job_title).to eq(job.title)
    end
  end

  describe '#search_data' do
    let!(:account) { create(:account) }
    let!(:user) { create(:user, account: account) }
    let!(:job) { create(:job, account: account, user: user) }
    let!(:job_user) { create(:job_user, user: user, job: job, account: account, person_function: "Lead Recruiter") }

    it 'returns correct search data structure' do
      data = job_user.search_data

      expect(data).to include(
        id: job_user.id,
        user_id: user.id,
        job_id: job.id,
        account_id: account.id,
        person_function: "lead recruiter"
      )
      expect(data[:user_name]).to eq(user.name.downcase)
      expect(data[:user_email]).to eq(user.email.downcase)
      expect(data[:job_title]).to eq(job.title.downcase)
    end
  end

  describe '.agg_search_array' do
    it 'returns aggregation fields' do
      agg = JobUser.agg_search_array

      expect(agg).to include(
        :user_id,
        :user_name,
        :job_id,
        :job_title,
        :person_function
      )
    end
  end

  describe 'split validation' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, account: account) }

    it 'allows split of 0' do
      job_user = build(:job_user, user: user, job: job, split: 0)
      expect(job_user).to be_valid
    end

    it 'allows split of 100' do
      job_user = build(:job_user, user: user, job: job, split: 100)
      expect(job_user).to be_valid
    end

    it 'does not allow split less than 0' do
      job_user = build(:job_user, user: user, job: job, split: -1)
      expect(job_user).not_to be_valid
    end

    it 'does not allow split greater than 100' do
      job_user = build(:job_user, user: user, job: job, split: 101)
      expect(job_user).not_to be_valid
    end
  end
end
