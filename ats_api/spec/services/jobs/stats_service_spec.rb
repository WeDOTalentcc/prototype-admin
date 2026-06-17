# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::StatsService do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  before do
    JobStatus.create_default_statuses
  end

  let(:active_status) { JobStatus.find_by(name: "Ativa") }
  let(:closed_status) { JobStatus.find_by(name: "Fechada (preenchida)") }
  let(:draft_status) { JobStatus.find_by(name: "Rascunho") }

  describe '#call' do
    before do
      create_list(:job, 3, user: user, account: account, job_status: active_status)
      create_list(:job, 2, user: user, account: account, job_status: closed_status)
      create(:job, user: user, account: account, job_status: draft_status)
    end

    subject { described_class.new(account_id: account.id).call }

    it 'returns by_status breakdown' do
      expect(subject[:by_status]).to be_an(Array)

      active_entry = subject[:by_status].find { |s| s[:status] == "Ativa" }
      expect(active_entry[:count]).to eq(3)
    end

    it 'returns open_vs_closed counts' do
      expect(subject[:open_vs_closed][:total]).to eq(6)
      expect(subject[:open_vs_closed][:closed]).to eq(2)
      expect(subject[:open_vs_closed][:open]).to eq(4)
    end

    it 'returns totals' do
      expect(subject[:totals][:total]).to eq(6)
    end

    it 'returns period info' do
      expect(subject[:period]).to have_key(:start_date)
      expect(subject[:period]).to have_key(:end_date)
    end

    it 'returns created_per_week' do
      expect(subject[:created_per_week]).to be_an(Array)
    end

    it 'returns by_priority' do
      expect(subject[:by_priority]).to be_an(Array)
    end

    it 'returns by_workplace_type' do
      expect(subject[:by_workplace_type]).to be_an(Array)
    end

    context 'with hiring managers' do
      let(:manager) { create(:user, account: account) }

      before do
        create_list(:job, 2, user: user, account: account, hiring_manager: manager)
      end

      it 'returns top_hiring_managers' do
        expect(subject[:top_hiring_managers]).to be_an(Array)
        expect(subject[:top_hiring_managers].first[:count]).to eq(2)
      end
    end

    context 'with date range' do
      it 'filters by period' do
        result = described_class.new(
          account_id: account.id,
          start_date: 1.day.ago.to_s,
          end_date: Date.current.to_s
        ).call

        expect(result[:totals][:created_in_period]).to be_a(Integer)
      end
    end
  end
end
