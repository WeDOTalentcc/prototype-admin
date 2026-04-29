# frozen_string_literal: true

require "rails_helper"

RSpec.describe ProcessSourcingJob, type: :job do
  let(:account) { instance_double(Account, id: 1, tenant: "test_tenant") }
  let(:user) { instance_double(User, id: 1) }
  let(:sourcing) do
    instance_double(
      Sourcing,
      id: 1,
      account_id: 1,
      user_id: 1,
      query: "Senior Developer",
      parameters: {},
      results_count: 1,
      status: "processing",
      local_results_count: 0,
      global_results_count: 0
    )
  end

  let(:pearch_profile_with_emails) do
    {
      docid: "test-profile-123",
      profile: {
        name: "John Doe",
        first_name: "John",
        last_name: "Doe",
        linkedin_slug: "johndoe",
        linkedin_url: "https://linkedin.com/in/johndoe",
        title: "Senior Developer",
        summary: "Experienced developer",
        business_emails: [ "john.doe@company.com", "j.doe@enterprise.com" ],
        personal_emails: [ "johndoe@gmail.com" ],
        has_emails: true
      }
    }
  end

  let(:pearch_profile_without_emails) do
    {
      docid: "test-profile-456",
      profile: {
        name: "Jane Smith",
        first_name: "Jane",
        last_name: "Smith",
        linkedin_slug: "janesmith",
        linkedin_url: "https://linkedin.com/in/janesmith",
        title: "Backend Engineer",
        summary: "Experienced engineer",
        business_emails: [],
        personal_emails: [],
        has_emails: false
      }
    }
  end

  let(:result_json_with_emails) do
    {
      uuid: "search-uuid-123",
      search_results: [ pearch_profile_with_emails ]
    }.to_json
  end

  let(:result_json_without_emails) do
    {
      uuid: "search-uuid-456",
      search_results: [ pearch_profile_without_emails ]
    }.to_json
  end

  let(:params_json) { {}.to_json }

  before do
    allow(Account).to receive(:find).with(1).and_return(account)
    allow(User).to receive(:find).with(1).and_return(user)
    allow(Sourcing).to receive(:find).with(1).and_return(sourcing)
    allow(Apartment::Tenant).to receive(:switch!)
    allow(sourcing).to receive(:update!)
    allow(sourcing).to receive(:"global_results_count=")
    allow(sourcing).to receive(:"local_results_count=")
    allow(Rails.logger).to receive(:info)
    allow(Rails.logger).to receive(:warn)
    allow_any_instance_of(described_class).to receive(:broadcast_processing_started)
    allow_any_instance_of(described_class).to receive(:broadcast_profiles_created)
    allow_any_instance_of(described_class).to receive(:broadcast_sourcing_profiles_found)
    allow_any_instance_of(described_class).to receive(:broadcast_global_search_completed)
  end

  describe "#extract_all_emails" do
    subject(:job) { described_class.new }

    context "quando profile tem business_emails e personal_emails" do
      it "retorna todos os emails com business primeiro" do
        profile_data = {
          business_emails: [ "work@company.com", "john@enterprise.com" ],
          personal_emails: [ "personal@gmail.com" ]
        }

        result = job.send(:extract_all_emails, profile_data)

        expect(result).to eq([ "work@company.com", "john@enterprise.com", "personal@gmail.com" ])
      end
    end

    context "quando profile tem apenas business_emails" do
      it "retorna apenas business emails" do
        profile_data = {
          business_emails: [ "work@company.com" ],
          personal_emails: []
        }

        result = job.send(:extract_all_emails, profile_data)

        expect(result).to eq([ "work@company.com" ])
      end
    end

    context "quando profile tem apenas personal_emails" do
      it "retorna apenas personal emails" do
        profile_data = {
          business_emails: [],
          personal_emails: [ "personal@gmail.com" ]
        }

        result = job.send(:extract_all_emails, profile_data)

        expect(result).to eq([ "personal@gmail.com" ])
      end
    end

    context "quando profile não tem emails" do
      it "retorna array vazio" do
        profile_data = {
          business_emails: [],
          personal_emails: []
        }

        result = job.send(:extract_all_emails, profile_data)

        expect(result).to eq([])
      end
    end

    context "quando profile tem emails duplicados" do
      it "remove duplicatas" do
        profile_data = {
          business_emails: [ "same@company.com" ],
          personal_emails: [ "same@company.com" ]
        }

        result = job.send(:extract_all_emails, profile_data)

        expect(result).to eq([ "same@company.com" ])
      end
    end

    context "quando profile tem emails em branco" do
      it "remove emails vazios" do
        profile_data = {
          business_emails: [ "work@company.com", "", nil ],
          personal_emails: [ "", "personal@gmail.com" ]
        }

        result = job.send(:extract_all_emails, profile_data)

        expect(result).to eq([ "work@company.com", "personal@gmail.com" ])
      end
    end
  end

  describe "#create_sourced_profile com emails" do
    let(:profile_matcher) { instance_double(SourcedProfiles::ProfileMatchingService) }
    let(:created_profile) do
      instance_double(
        SourcedProfile,
        id: 1,
        email: "john.doe@company.com",
        emails: [ "john.doe@company.com", "j.doe@enterprise.com", "johndoe@gmail.com" ]
      )
    end

    before do
      allow(SourcedProfiles::ProfileMatchingService).to receive(:new).and_return(profile_matcher)
      allow(profile_matcher).to receive(:find_duplicate).and_return(nil)
      allow(SourcedProfile).to receive(:create!).and_return(created_profile)
      allow_any_instance_of(described_class).to receive(:create_or_update_sourced_profile_sourcing)
    end

    it "salva o array de emails em SourcedProfile.emails" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          emails: [ "john.doe@company.com", "j.doe@enterprise.com", "johndoe@gmail.com" ]
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Senior Developer", result_json_with_emails, params_json, 1)
    end

    it "salva o primeiro email em SourcedProfile.email" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          email: "john.doe@company.com"
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Senior Developer", result_json_with_emails, params_json, 1)
    end

    it "marca has_emails como true quando existem emails" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          has_emails: true
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Senior Developer", result_json_with_emails, params_json, 1)
    end
  end

  describe "#create_sourced_profile sem emails" do
    let(:profile_matcher) { instance_double(SourcedProfiles::ProfileMatchingService) }
    let(:created_profile) do
      instance_double(
        SourcedProfile,
        id: 2,
        email: nil,
        emails: []
      )
    end

    before do
      allow(SourcedProfiles::ProfileMatchingService).to receive(:new).and_return(profile_matcher)
      allow(profile_matcher).to receive(:find_duplicate).and_return(nil)
      allow(SourcedProfile).to receive(:create!).and_return(created_profile)
      allow_any_instance_of(described_class).to receive(:create_or_update_sourced_profile_sourcing)
    end

    it "salva array vazio em SourcedProfile.emails" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          emails: []
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Backend Engineer", result_json_without_emails, params_json, 1)
    end

    it "salva nil em SourcedProfile.email" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          email: nil
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Backend Engineer", result_json_without_emails, params_json, 1)
    end

    it "marca has_emails como false quando não existem emails" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          has_emails: false
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Backend Engineer", result_json_without_emails, params_json, 1)
    end
  end

  describe "logging de emails" do
    let(:profile_matcher) { instance_double(SourcedProfiles::ProfileMatchingService) }
    let(:created_profile) do
      instance_double(
        SourcedProfile,
        id: 1,
        email: "john.doe@company.com",
        emails: [ "john.doe@company.com", "j.doe@enterprise.com", "johndoe@gmail.com" ]
      )
    end

    before do
      allow(SourcedProfiles::ProfileMatchingService).to receive(:new).and_return(profile_matcher)
      allow(profile_matcher).to receive(:find_duplicate).and_return(nil)
      allow(SourcedProfile).to receive(:create!).and_return(created_profile)
      allow_any_instance_of(described_class).to receive(:create_or_update_sourced_profile_sourcing)
    end

    it "loga a quantidade de emails e o email principal" do
      job = described_class.new

      expect(Rails.logger).to receive(:info).with(
        "[ProcessSourcingJob] 📧 Emails found: 3 (primary: john.doe@company.com)"
      )

      job.perform(1, 1, "Senior Developer", result_json_with_emails, params_json, 1)
    end
  end
end
