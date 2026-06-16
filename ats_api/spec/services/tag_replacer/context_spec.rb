# frozen_string_literal: true

require "rails_helper"

RSpec.describe TagReplacer::Context do
  let(:candidate) { double("Candidate", name: "Maria") }
  let(:job)       { double("Job", title: "Engineer") }
  let(:user)      { double("User", name: "João") }
  let(:record)    { { candidate: candidate, job: job, user: user } }

  subject(:context) { described_class.new(record) }

  describe "#fetch" do
    it "returns the entity for a known key" do
      expect(context.fetch(:candidate)).to eq(candidate)
    end

    it "returns nil for an unknown key" do
      expect(context.fetch(:unknown_entity)).to be_nil
    end

    it "returns nil when entity_key is nil" do
      expect(context.fetch(nil)).to be_nil
    end

    it "caches the resolved entity on subsequent calls" do
      first  = context.fetch(:candidate)
      second = context.fetch(:candidate)
      expect(first).to be(second)
    end

    it "falls back to :user when :recruiter record is absent but recruiter_id is nil" do
      ctx = described_class.new({ user: user })
      expect(ctx.fetch(:user)).to eq(user)
    end

    it "resolves :client_company from :job when not directly in record" do
      company = double("Business", name: "Acme")
      allow(job).to receive(:client_company).and_return(company)
      ctx = described_class.new({ job: job })
      expect(ctx.fetch(:client_company)).to eq(company)
    end
  end

  describe "#preload" do
    it "preloads multiple entity keys into cache" do
      context.preload([ :candidate, :job ])
      expect(context.fetch(:candidate)).to eq(candidate)
      expect(context.fetch(:job)).to eq(job)
    end
  end

  describe "#recruiter" do
    it "returns nil when no recruiter_id is provided" do
      expect(context.recruiter).to be_nil
    end

    it "looks up recruiter by id when recruiter_id is given" do
      recruiter = double("User", name: "Recruiter X")
      allow(User).to receive(:find_by).with(id: 42).and_return(recruiter)

      ctx = described_class.new({}, 42)
      expect(ctx.recruiter).to eq(recruiter)
    end
  end
end
