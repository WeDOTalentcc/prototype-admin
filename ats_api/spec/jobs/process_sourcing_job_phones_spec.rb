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

  let(:pearch_profile_with_phones) do
    {
      docid: "test-profile-789",
      profile: {
        name: "Maria Silva",
        first_name: "Maria",
        last_name: "Silva",
        linkedin_slug: "mariasilva",
        linkedin_url: "https://linkedin.com/in/mariasilva",
        title: "Tech Lead",
        summary: "Experienced developer",
        phone_number: "+55 11 99999-9999",
        phone_numbers: [ "+55 11 99999-9999", "+55 11 88888-8888" ],
        has_phone_numbers: true
      }
    }
  end

  let(:pearch_profile_without_phones) do
    {
      docid: "test-profile-890",
      profile: {
        name: "João Santos",
        first_name: "João",
        last_name: "Santos",
        linkedin_slug: "joaosantos",
        linkedin_url: "https://linkedin.com/in/joaosantos",
        title: "Software Engineer",
        summary: "Experienced engineer",
        phone_numbers: [],
        has_phone_numbers: false
      }
    }
  end

  let(:result_json_with_phones) do
    {
      uuid: "search-uuid-789",
      search_results: [ pearch_profile_with_phones ]
    }.to_json
  end

  let(:result_json_without_phones) do
    {
      uuid: "search-uuid-890",
      search_results: [ pearch_profile_without_phones ]
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

  describe "#extract_all_phones" do
    subject(:job) { described_class.new }

    context "quando profile tem phone_numbers" do
      it "retorna todos os telefones" do
        profile_data = {
          phone_numbers: [ "+55 11 99999-9999", "+55 11 88888-8888", "+55 11 77777-7777" ]
        }

        result = job.send(:extract_all_phones, profile_data)

        expect(result).to eq([ "+55 11 99999-9999", "+55 11 88888-8888", "+55 11 77777-7777" ])
      end
    end

    context "quando profile tem apenas um telefone" do
      it "retorna array com um telefone" do
        profile_data = {
          phone_numbers: [ "+55 11 99999-9999" ]
        }

        result = job.send(:extract_all_phones, profile_data)

        expect(result).to eq([ "+55 11 99999-9999" ])
      end
    end

    context "quando profile não tem telefones" do
      it "retorna array vazio" do
        profile_data = {
          phone_numbers: []
        }

        result = job.send(:extract_all_phones, profile_data)

        expect(result).to eq([])
      end
    end

    context "quando profile tem telefones duplicados" do
      it "remove duplicatas" do
        profile_data = {
          phone_numbers: [ "+55 11 99999-9999", "+55 11 99999-9999" ]
        }

        result = job.send(:extract_all_phones, profile_data)

        expect(result).to eq([ "+55 11 99999-9999" ])
      end
    end

    context "quando profile tem telefones em branco" do
      it "remove telefones vazios" do
        profile_data = {
          phone_numbers: [ "+55 11 99999-9999", "", nil, "+55 11 88888-8888" ]
        }

        result = job.send(:extract_all_phones, profile_data)

        expect(result).to eq([ "+55 11 99999-9999", "+55 11 88888-8888" ])
      end
    end
  end

  describe "#create_sourced_profile com telefones" do
    let(:profile_matcher) { instance_double(SourcedProfiles::ProfileMatchingService) }
    let(:created_profile) do
      instance_double(
        SourcedProfile,
        id: 1,
        phone: "+55 11 99999-9999",
        phones: [ "+55 11 99999-9999", "+55 11 88888-8888" ]
      )
    end

    before do
      allow(SourcedProfiles::ProfileMatchingService).to receive(:new).and_return(profile_matcher)
      allow(profile_matcher).to receive(:find_duplicate).and_return(nil)
      allow(SourcedProfile).to receive(:create!).and_return(created_profile)
      allow_any_instance_of(described_class).to receive(:create_or_update_sourced_profile_sourcing)
    end

    it "salva o array de telefones em SourcedProfile.phones" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          phones: [ "+55 11 99999-9999", "+55 11 88888-8888" ]
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Tech Lead", result_json_with_phones, params_json, 1)
    end

    it "salva o primeiro telefone em SourcedProfile.phone" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          phone: "+55 11 99999-9999"
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Tech Lead", result_json_with_phones, params_json, 1)
    end

    it "marca has_phone_numbers como true quando existem telefones" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          has_phone_numbers: true
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Tech Lead", result_json_with_phones, params_json, 1)
    end
  end

  describe "#create_sourced_profile sem telefones" do
    let(:profile_matcher) { instance_double(SourcedProfiles::ProfileMatchingService) }
    let(:created_profile) do
      instance_double(
        SourcedProfile,
        id: 2,
        phone: nil,
        phones: []
      )
    end

    before do
      allow(SourcedProfiles::ProfileMatchingService).to receive(:new).and_return(profile_matcher)
      allow(profile_matcher).to receive(:find_duplicate).and_return(nil)
      allow(SourcedProfile).to receive(:create!).and_return(created_profile)
      allow_any_instance_of(described_class).to receive(:create_or_update_sourced_profile_sourcing)
    end

    it "salva array vazio em SourcedProfile.phones" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          phones: []
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Software Engineer", result_json_without_phones, params_json, 1)
    end

    it "salva nil em SourcedProfile.phone" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          phone: nil
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Software Engineer", result_json_without_phones, params_json, 1)
    end

    it "marca has_phone_numbers como false quando não existem telefones" do
      job = described_class.new

      expect(SourcedProfile).to receive(:create!).with(
        hash_including(
          has_phone_numbers: false
        )
      ).and_return(created_profile)

      job.perform(1, 1, "Software Engineer", result_json_without_phones, params_json, 1)
    end
  end

  describe "logging de telefones" do
    let(:profile_matcher) { instance_double(SourcedProfiles::ProfileMatchingService) }
    let(:created_profile) do
      instance_double(
        SourcedProfile,
        id: 1,
        phone: "+55 11 99999-9999",
        phones: [ "+55 11 99999-9999", "+55 11 88888-8888" ]
      )
    end

    before do
      allow(SourcedProfiles::ProfileMatchingService).to receive(:new).and_return(profile_matcher)
      allow(profile_matcher).to receive(:find_duplicate).and_return(nil)
      allow(SourcedProfile).to receive(:create!).and_return(created_profile)
      allow_any_instance_of(described_class).to receive(:create_or_update_sourced_profile_sourcing)
    end

    it "loga a quantidade de telefones e o telefone principal" do
      job = described_class.new

      expect(Rails.logger).to receive(:info).with(
        "[ProcessSourcingJob] 📱 Phones found: 2 (primary: +55 11 99999-9999)"
      )

      job.perform(1, 1, "Tech Lead", result_json_with_phones, params_json, 1)
    end
  end
end
