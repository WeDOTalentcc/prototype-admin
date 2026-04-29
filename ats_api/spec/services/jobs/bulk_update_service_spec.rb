# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::BulkUpdateService do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  before do
    allow(Current).to receive(:user).and_return(user)
    allow(Current).to receive(:ip).and_return('127.0.0.1')
  end

  let!(:jobs) { create_list(:job, 3, user: user, account: account) }

  describe '#call' do
    context 'with valid fields' do
      it 'updates all specified jobs' do
        result = described_class.new(
          job_ids: jobs.map(&:id),
          fields: { "priority" => 1 },
          user: user
        ).call

        expect(result[:success]).to be true
        expect(result[:updated]).to eq(3)
        expect(result[:failed]).to eq(0)
        expect(result[:batch_id]).to be_present

        jobs.each do |job|
          expect(job.reload.priority).to eq(1)
        end
      end

      it 'updates hiring_manager_id' do
        manager = create(:user, account: account)

        result = described_class.new(
          job_ids: jobs.map(&:id),
          fields: { "hiring_manager_id" => manager.id },
          user: user
        ).call

        expect(result[:success]).to be true
        jobs.each do |job|
          expect(job.reload.hiring_manager_id).to eq(manager.id)
        end
      end
    end

    context 'with activity log tracking' do
      it 'creates activity logs with bulk_update category' do
        expect {
          described_class.new(
            job_ids: jobs.map(&:id),
            fields: { "priority" => 2 },
            user: user
          ).call
        }.to change(ActivityLog, :count).by(3)

        logs = ActivityLog.where(reference_type: "Job", reference_id: jobs.map(&:id))
        expect(logs.all? { |l| l.category.start_with?("bulk_update:") }).to be true

        batch_ids = logs.map { |l| l.category.split(":").last }.uniq
        expect(batch_ids.size).to eq(1)
      end
    end

    context 'with disallowed fields' do
      it 'filters out non-whitelisted fields' do
        result = described_class.new(
          job_ids: jobs.map(&:id),
          fields: { "title" => "Hacked", "priority" => 1 },
          user: user
        ).call

        expect(result[:success]).to be true
        jobs.each do |job|
          expect(job.reload.title).not_to eq("Hacked")
          expect(job.reload.priority).to eq(1)
        end
      end
    end

    context 'with empty fields' do
      it 'returns error' do
        result = described_class.new(
          job_ids: jobs.map(&:id),
          fields: { "title" => "Not allowed" },
          user: user
        ).call

        expect(result[:success]).to be false
        expect(result[:error]).to include("Nenhum campo válido")
      end
    end

    context 'with empty job_ids' do
      it 'returns error' do
        result = described_class.new(
          job_ids: [],
          fields: { "priority" => 1 },
          user: user
        ).call

        expect(result[:success]).to be false
        expect(result[:error]).to include("Nenhuma vaga")
      end
    end

    context 'with deleted jobs' do
      before { jobs.first.update_column(:is_deleted, true) }

      it 'skips deleted jobs' do
        result = described_class.new(
          job_ids: jobs.map(&:id),
          fields: { "priority" => 1 },
          user: user
        ).call

        expect(result[:success]).to be true
        expect(result[:updated]).to eq(2)
      end
    end
  end
end
