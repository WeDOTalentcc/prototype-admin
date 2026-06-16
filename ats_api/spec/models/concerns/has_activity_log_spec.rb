# frozen_string_literal: true

require 'rails_helper'

RSpec.describe HasActivityLog, type: :model do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:job) { create(:job, account: account) }

  before do
    allow(Current).to receive(:user).and_return(user)
    allow(Current).to receive(:ip).and_return('127.0.0.1')
  end

  describe 'when included in a model' do
    it 'logs activity on create' do
      expect {
        create(:job, title: 'Test Job', account: account)
      }.to change(ActivityLog, :count).by(1)

      activity_log = ActivityLog.last
      expect(activity_log.action).to eq('create')
      expect(activity_log.reference_type).to eq('Job')
      expect(activity_log.user).to eq(user)
      expect(activity_log.account).to eq(user.account)
      expect(activity_log.ip_address).to eq('127.0.0.1')
    end

    it 'logs activity on update' do
      job = create(:job, title: 'Original Title', account: account)

      expect {
        job.update!(title: 'Updated Title')
      }.to change(ActivityLog, :count).by(1)

      activity_log = ActivityLog.last
      expect(activity_log.action).to eq('update')
      expect(activity_log.reference_type).to eq('Job')
      expect(activity_log.reference_id).to eq(job.id)
      expect(activity_log.changeset['title']['from']).to eq('Original Title')
      expect(activity_log.changeset['title']['to']).to eq('Updated Title')
    end

    it 'does not log activity on update if no changes' do
      job = create(:job, title: 'Same Title', account: account)

      expect {
        job.update!(title: 'Same Title')
      }.not_to change(ActivityLog, :count)
    end

    it 'logs activity on destroy' do
      job = create(:job, title: 'Job to Delete', account: account)
      job_id = job.id

      expect {
        job.destroy!
      }.to change(ActivityLog, :count).by(1)

      activity_log = ActivityLog.last
      expect(activity_log.action).to eq('destroy')
      expect(activity_log.reference_type).to eq('Job')
      expect(activity_log.reference_id).to eq(job_id)
    end

    it 'excludes updated_at and created_at from changeset' do
      job = create(:job, title: 'Original Title', account: account)

      job.update!(title: 'Updated Title')

      activity_log = ActivityLog.last
      expect(activity_log.changeset).not_to have_key('updated_at')
      expect(activity_log.changeset).not_to have_key('created_at')
      expect(activity_log.changeset).to have_key('title')
    end

    it 'formats changeset correctly' do
      job = create(:job, title: 'Original Title', description: 'Original Description', account: account)

      job.update!(title: 'Updated Title', description: 'Updated Description')

      activity_log = ActivityLog.last
      expect(activity_log.changeset['title']).to eq({
        'from' => 'Original Title',
        'to' => 'Updated Title'
      })
      expect(activity_log.changeset['description']).to eq({
        'from' => 'Original Description',
        'to' => 'Updated Description'
      })
    end

    context 'when Current.user is nil' do
      before do
        allow(Current).to receive(:user).and_return(nil)
      end

      it 'still creates activity log without user' do
        expect {
          create(:job, title: 'Test Job', account: account)
        }.to change(ActivityLog, :count).by(1)

        activity_log = ActivityLog.last
        expect(activity_log.user).to be_nil
        expect(activity_log.account).to be_nil
      end
    end

    context 'integration with rollback' do
      it 'can rollback changes made by HasActivityLog' do
        job = create(:job, title: 'Original Title', account: account)
        job.update!(title: 'Updated Title')

        activity_log = ActivityLog.where(
          reference_type: 'Job',
          reference_id: job.id,
          action: 'update'
        ).last

        activity_log.rollback!(current_user: user)

        expect(job.reload.title).to eq('Original Title')
      end
    end
  end
end
