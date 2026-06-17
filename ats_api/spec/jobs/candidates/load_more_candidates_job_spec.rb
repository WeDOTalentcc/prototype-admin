# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::LoadMoreCandidatesJob do
  subject(:job) { described_class.new }

  let(:account) { instance_double(Account, id: 1, tenant: "test_tenant") }
  let(:user) { instance_double(User, id: 10) }
  let(:sourcing) do
    instance_double(
      Sourcing,
      id: 100,
      user_id: 10,
      parameters: { "sources" => [ "local" ] },
      sourced_profiles: sourced_profiles_relation,
      sourced_profile_sourcings: sps_relation,
      local_results_count: 0,
      global_results_count: 0,
      update!: true
    )
  end

  let(:sourced_profiles_relation) { instance_double(ActiveRecord::Relation) }
  let(:sps_relation) { double("sps_relation", active: active_relation) }
  let(:active_relation) { double("active_relation", count: 6) }

  let(:candidate1) do
    instance_double(
      Candidate, id: 101, name: "Alice", email: "alice@example.com",
      phone: "11999999999", mobile_phone: nil, cpf: nil, date_birth: nil,
      role_name: "Developer", self_introduction: "Dev", avatar_public_url: nil,
      gender: nil, marital_status: nil, city: "SP", state: "SP", country: "BR",
      remote_work: true, mobility: false, current_company: "Acme",
      position_level: "senior", curriculum_text: "text",
      linkedin_slug: nil, linkedin: nil
    )
  end

  let(:candidate2) do
    instance_double(
      Candidate, id: 102, name: "Bob", email: "bob@example.com",
      phone: "11888888888", mobile_phone: nil, cpf: nil, date_birth: nil,
      role_name: "Designer", self_introduction: "Design", avatar_public_url: nil,
      gender: nil, marital_status: nil, city: "RJ", state: "RJ", country: "BR",
      remote_work: false, mobility: true, current_company: "Corp",
      position_level: "mid", curriculum_text: "design text",
      linkedin_slug: nil, linkedin: nil
    )
  end

  let(:cache_data) do
    {
      candidate_ids: [ 1, 2, 3, 101, 102, 103, 201, 202, 203 ],
      search_meta_by_id: { 101 => { source: "hybrid", score: 0.9 }, 102 => { source: "es", score: 0.8 } },
      total: 9,
      page_size: 3,
      created_at: Time.current.iso8601,
      expires_at: 30.minutes.from_now.iso8601
    }
  end

  before do
    allow(Account).to receive(:find).with(1).and_return(account)
    allow(User).to receive(:find).with(10).and_return(user)
    allow(Apartment::Tenant).to receive(:switch).with("test_tenant").and_yield
    allow(Sourcing).to receive(:find).with(100).and_return(sourcing)
    allow(SourcingChannel).to receive(:broadcast_to)
    allow(Rails.logger).to receive(:info)
    allow(Rails.logger).to receive(:error)
  end

  describe "#perform" do
    context "when pool cache exists" do
      before do
        allow(Rails.cache).to receive(:read).with("sourcing_pool:100:local").and_return(cache_data)
        allow(Rails.cache).to receive(:read).with("sourcing_pool:100:global").and_return(nil)

        candidates_relation = double("candidates_relation")
        allow(Candidate).to receive(:where).with(id: [ 101, 102, 103 ]).and_return(candidates_relation)
        allow(candidates_relation).to receive(:index_by).and_return({ 101 => candidate1, 102 => candidate2 })

        allow(sourced_profiles_relation).to receive(:find_by).and_return(nil)
        allow(SourcedProfiles::ProfileMatchingService).to receive_message_chain(:new, :find_duplicate).and_return(nil)
        allow(SourcedProfiles::CandidateEnrichmentService).to receive(:call)

        profile = instance_double(SourcedProfile, id: 50, provider: "local", curriculum_text: "text")
        allow(SourcedProfile).to receive(:new).and_return(profile)
        allow(profile).to receive(:save!)
        allow(SourcedProfileSourcing).to receive(:create!)
      end

      it "processes page 2 candidates" do
        job.perform(1, 10, 100, 2, 3)

        expect(SourcingChannel).to have_received(:broadcast_to).with(
          "10_sourcing_100",
          hash_including(type: "profiles_processing_started")
        )
      end

      it "broadcasts load_more_completed" do
        job.perform(1, 10, 100, 2, 3)

        expect(SourcingChannel).to have_received(:broadcast_to).with(
          "10_sourcing_100",
          hash_including(type: "load_more_completed", page: 2, total_pages: 3)
        )
      end

      it "updates sourcing processed_count" do
        allow(active_relation).to receive(:where).with(source: "local").and_return(
          double(count: 6)
        )
        allow(active_relation).to receive(:where).with(source: "global").and_return(
          double(count: 0)
        )

        job.perform(1, 10, 100, 2, 3)

        expect(sourcing).to have_received(:update!).with(
          processed_count: 6,
          results_count: 6,
          local_results_count: 6,
          global_results_count: 0
        )
      end
    end

    context "when pool cache is expired" do
      before do
        allow(Rails.cache).to receive(:read).with("sourcing_pool:100:local").and_return(nil)
        allow(Rails.cache).to receive(:read).with("sourcing_pool:100:global").and_return(nil)
      end

      it "broadcasts pool expired" do
        job.perform(1, 10, 100, 2, 3)

        expect(SourcingChannel).to have_received(:broadcast_to).with(
          "10_sourcing_100",
          { type: "sourcing_pool_expired", sourcing_id: 100 }
        )
      end
    end

    context "when page exceeds available candidates" do
      before do
        allow(Rails.cache).to receive(:read).with("sourcing_pool:100:local").and_return(cache_data)
        allow(Rails.cache).to receive(:read).with("sourcing_pool:100:global").and_return(nil)
      end

      it "broadcasts pool expired for out-of-range page" do
        job.perform(1, 10, 100, 10, 3)

        expect(SourcingChannel).to have_received(:broadcast_to).with(
          "10_sourcing_100",
          { type: "sourcing_pool_expired", sourcing_id: 100 }
        )
      end
    end

    context "when an error occurs" do
      before do
        allow(Rails.cache).to receive(:read).and_raise(StandardError.new("Redis down"))
        allow(Sourcing).to receive(:find_by).with(id: 100).and_return(sourcing)
      end

      it "broadcasts load_more_failed" do
        job.perform(1, 10, 100, 2, 3)

        expect(SourcingChannel).to have_received(:broadcast_to).with(
          "10_sourcing_100",
          hash_including(type: "load_more_failed", error: "Redis down")
        )
      end
    end
  end
end
