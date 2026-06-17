# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::CopyByAmountJob, type: :job do
  include ActiveJob::TestHelper

  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user) }

  describe '#perform' do
    before do
      allow(Jobs::CopyService).to receive(:copy_multiple)
    end

    it 'calls CopyService.copy_multiple with correct params' do
      described_class.perform_now(5, job.id, user.id, [])

      expect(Jobs::CopyService).to have_received(:copy_multiple).with(
        amount: 5,
        job_id: job.id,
        user_id: user.id,
        entities: []
      )
    end

    it 'can be enqueued' do
      expect {
        described_class.perform_later(3, job.id, user.id, [ "language_relationships" ])
      }.to have_enqueued_job(described_class)
        .with(3, job.id, user.id, [ "language_relationships" ])
    end
  end
end
