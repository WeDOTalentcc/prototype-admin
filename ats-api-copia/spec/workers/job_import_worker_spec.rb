# frozen_string_literal: true

require 'rails_helper'

RSpec.describe JobImportWorker do
  subject(:worker) { described_class.new }

  let(:valid_payload) do
    {
      "payload" => {
        "provider" => "gupy",
        "provider_job_id" => "ext-123",
        "name" => "Software Engineer",
        "description" => "Build things",
        "company_id" => 10,
        "account_id" => 42,
        "user_id" => 7,
        "is_remote" => true,
        "city" => "São Paulo",
        "state" => "SP",
        "country" => "BR"
      }
    }.to_json
  end

  describe '#work' do
    it 'creates a job with account_id and user_id from payload' do
      result = worker.work(valid_payload)

      job = Job.find_by(provider: "gupy", provider_job_id: "ext-123")
      expect(job).to be_present
      expect(job.account_id).to eq(42)
      expect(job.user_id).to eq(7)
    end

    it 'rejects payload without account_id' do
      payload = JSON.parse(valid_payload)
      payload["payload"].delete("account_id")

      result = worker.work(payload.to_json)

      expect(Job.find_by(provider_job_id: "ext-123")).to be_nil
    end

    it 'rejects payload without user_id' do
      payload = JSON.parse(valid_payload)
      payload["payload"].delete("user_id")

      result = worker.work(payload.to_json)

      expect(Job.find_by(provider_job_id: "ext-123")).to be_nil
    end
  end
end
