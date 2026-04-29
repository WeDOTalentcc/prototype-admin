# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SearchProcessing do
  let(:dummy_class) do
    Class.new do
      include Candidates::SearchProcessing

      def initialize(account, user)
        @account = account
        @user = user
      end
    end
  end

  let(:account) { instance_double(Account, id: 1, tenant: "test_tenant") }
  let(:user) { instance_double(User, id: 10) }
  let(:service) { dummy_class.new(account, user) }

  let(:sourcing) do
    instance_double(
      Sourcing,
      id: 100,
      user_id: 10,
      sourced_profiles: sourced_profiles_relation,
      update!: true
    )
  end

  let(:sourced_profiles_relation) { instance_double(ActiveRecord::Relation) }

  let(:candidate) do
    instance_double(
      Candidate,
      id: 1,
      name: "John Doe",
      email: "john@example.com",
      phone: "11999999999",
      mobile_phone: nil,
      cpf: nil,
      date_birth: nil,
      role_name: "Developer",
      self_introduction: "Experienced developer",
      avatar_public_url: nil,
      gender: nil,
      marital_status: nil,
      city: "São Paulo",
      state: "SP",
      country: "Brazil",
      remote_work: true,
      mobility: false,
      current_company: "Acme",
      position_level: "senior",
      curriculum_text: "Full stack developer with 5 years",
      linkedin_slug: "johndoe",
      linkedin: nil
    )
  end

  before do
    allow(SourcingChannel).to receive(:broadcast_to)
    allow(Rails.logger).to receive(:info)
    allow(Rails.logger).to receive(:error)
  end

  describe "#process_candidates_batch" do
    before do
      allow(sourced_profiles_relation).to receive(:find_by).and_return(nil)
      allow(SourcedProfiles::ProfileMatchingService).to receive_message_chain(:new, :find_duplicate).and_return(nil)
      allow(SourcedProfiles::CandidateEnrichmentService).to receive(:call)
    end

    context "when candidates are provided" do
      let(:profile) { instance_double(SourcedProfile, id: 50, provider: "local", curriculum_text: "text") }

      before do
        allow(SourcedProfile).to receive(:new).and_return(profile)
        allow(profile).to receive(:save!)
        allow(SourcedProfileSourcing).to receive(:create!)
      end

      it "returns the count of processed candidates" do
        result = service.send(:process_candidates_batch, [ candidate ], sourcing, account, user)

        expect(result).to eq(1)
      end

      it "broadcasts processing started" do
        service.send(:process_candidates_batch, [ candidate ], sourcing, account, user)

        expect(SourcingChannel).to have_received(:broadcast_to).with(
          "10_sourcing_100",
          hash_including(type: "profiles_processing_started")
        )
      end
    end

    context "when candidate processing raises an error" do
      before do
        allow(sourced_profiles_relation).to receive(:find_by).and_raise(StandardError.new("DB error"))
      end

      it "counts as failed and continues" do
        result = service.send(:process_candidates_batch, [ candidate ], sourcing, account, user)

        expect(result).to eq(0)
      end
    end

    context "when candidates list is empty" do
      it "returns zero" do
        result = service.send(:process_candidates_batch, [], sourcing, account, user)

        expect(result).to eq(0)
      end
    end
  end

  describe "#broadcast_load_more_completed" do
    it "broadcasts with correct pagination info" do
      service.send(:broadcast_load_more_completed, sourcing, 30, 2, 5, 150)

      expect(SourcingChannel).to have_received(:broadcast_to).with(
        "10_sourcing_100",
        {
          type: "load_more_completed",
          sourcing_id: 100,
          loaded: 30,
          page: 2,
          total_pages: 5,
          total_in_pool: 150,
          has_more: true
        }
      )
    end

    it "sets has_more to false on last page" do
      service.send(:broadcast_load_more_completed, sourcing, 30, 5, 5, 150)

      expect(SourcingChannel).to have_received(:broadcast_to).with(
        "10_sourcing_100",
        hash_including(has_more: false, page: 5, total_pages: 5)
      )
    end
  end

  describe "#broadcast_pool_expired" do
    it "broadcasts pool expired event" do
      service.send(:broadcast_pool_expired, sourcing)

      expect(SourcingChannel).to have_received(:broadcast_to).with(
        "10_sourcing_100",
        { type: "sourcing_pool_expired", sourcing_id: 100 }
      )
    end
  end
end
