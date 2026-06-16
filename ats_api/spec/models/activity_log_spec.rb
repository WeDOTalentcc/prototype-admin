# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ActivityLog, type: :model do
  let(:user) { create(:user) }
  let(:account) { create(:account) }
  let(:job) { create(:job, account: account) }

  describe 'associations' do
    it { should belong_to(:user).optional }
    it { should belong_to(:account).optional }
  end

  describe 'validations' do
    it 'creates a valid activity log' do
      activity_log = described_class.new(
        reference_type: 'Job',
        reference_id: job.id,
        action: 'create',
        changeset: { 'title' => { 'from' => nil, 'to' => 'New Job' } },
        user: user,
        account: account
      )
      expect(activity_log).to be_valid
    end
  end

  describe '.log_change' do
    it 'creates an activity log with all parameters' do
      changeset = { 'title' => { 'from' => 'Old Title', 'to' => 'New Title' } }

      activity_log = described_class.log_change(
        job,
        user: user,
        action: 'update',
        changeset: changeset,
        account: account,
        ip: '127.0.0.1'
      )

      expect(activity_log).to be_persisted
      expect(activity_log.reference_type).to eq('Job')
      expect(activity_log.reference_id).to eq(job.id)
      expect(activity_log.action).to eq('update')
      expect(activity_log.changeset).to eq(changeset)
      expect(activity_log.user).to eq(user)
      expect(activity_log.account).to eq(account)
      expect(activity_log.ip_address).to eq('127.0.0.1')
    end

    it 'uses user account when account is not provided' do
      user_with_account = create(:user, account: account)

      activity_log = described_class.log_change(
        job,
        user: user_with_account,
        action: 'create',
        changeset: {},
        account: nil
      )

      expect(activity_log.account).to eq(account)
    end
  end

  describe '#rollback!' do
    let(:original_title) { 'Original Title' }
    let(:updated_title) { 'Updated Title' }
    let(:changeset) do
      { 'title' => { 'from' => original_title, 'to' => updated_title } }
    end
    let(:activity_log) do
      create(:activity_log,
             reference_type: 'Job',
             reference_id: job.id,
             action: 'update',
             changeset: changeset,
             user: user,
             account: account)
    end

    before do
      job.update!(title: updated_title)
    end

    it 'rolls back the changes successfully' do
      expect { activity_log.rollback!(current_user: user) }
        .to change { job.reload.title }.from(updated_title).to(original_title)
    end

    it 'creates a rollback activity log' do
      initial_count = ActivityLog.count

      activity_log.rollback!(current_user: user)

      rollback_logs = ActivityLog.where(action: 'rollback', rolled_back_from_id: activity_log.id)
      expect(rollback_logs.count).to eq(1)

      rollback_log = rollback_logs.first
      expect(rollback_log.action).to eq('rollback')
      expect(rollback_log.reference_type).to eq('Job')
      expect(rollback_log.reference_id).to eq(job.id)
      expect(rollback_log.user).to eq(user)
      expect(rollback_log.rolled_back_from_id).to eq(activity_log.id)
    end

    it 'handles array format changeset' do
      array_changeset = { 'title' => [ original_title, updated_title ] }
      activity_log.update!(changeset: array_changeset)

      expect { activity_log.rollback!(current_user: user) }
        .to change { job.reload.title }.from(updated_title).to(original_title)
    end

    it 'raises error for non-update actions' do
      activity_log.update!(action: 'create')

      expect { activity_log.rollback!(current_user: user) }
        .to raise_error('Rollback only allowed for update actions')
    end

    it 'raises error when record is not found' do
      activity_log.update!(reference_id: 99999)

      expect { activity_log.rollback!(current_user: user) }
        .to raise_error(ActiveRecord::RecordNotFound, 'Record not found')
    end

    context 'with complex changeset' do
      let(:complex_changeset) do
        {
          'title' => { 'from' => 'Old Title', 'to' => 'New Title' },
          'description' => { 'from' => 'Old Desc', 'to' => 'New Desc' }
        }
      end

      before do
        activity_log.update!(changeset: complex_changeset)
        job.update!(title: 'New Title', description: 'New Desc')
      end

      it 'rolls back multiple fields' do
        activity_log.rollback!(current_user: user)
        job.reload

        expect(job.title).to eq('Old Title')
        expect(job.description).to eq('Old Desc')
      end
    end
  end

  describe 'search integration' do
    it 'includes Searchable concern' do
      expect(ActivityLog.ancestors).to include(Searchable)
    end

    it 'excludes changeset from search data' do
      activity_log = create(:activity_log,
                           changeset: { 'title' => { 'from' => 'a', 'to' => 'b' } },
                           user: user,
                           account: account)

      search_data = activity_log.search_data
      expect(search_data).not_to have_key('changeset')
      expect(search_data).to have_key(:user_name)
      expect(search_data).to have_key(:account_name)
    end
  end
end
