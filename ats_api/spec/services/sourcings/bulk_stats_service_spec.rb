# frozen_string_literal: true

require "rails_helper"

RSpec.describe Sourcings::BulkStatsService, type: :service do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  let!(:sourcing1) { create(:sourcing, account: account, user: user, status: "done") }
  let!(:sourcing2) { create(:sourcing, account: account, user: user, status: "done") }

  let!(:profile1) { create(:sourced_profile, :with_candidate, account: account, external_id: "ext_1") }
  let!(:profile2) { create(:sourced_profile, account: account, external_id: "ext_2") }
  let!(:profile3) { create(:sourced_profile, account: account, external_id: "ext_3") }

  let!(:sps1) { create(:sourced_profile_sourcing, sourced_profile: profile1, sourcing: sourcing1, account: account, user: user, score: 92) }
  let!(:sps2) { create(:sourced_profile_sourcing, sourced_profile: profile2, sourcing: sourcing1, account: account, user: user, score: 78) }
  let!(:sps3) { create(:sourced_profile_sourcing, sourced_profile: profile3, sourcing: sourcing2, account: account, user: user, score: 65) }

  before do
    Apartment::Tenant.switch!(account.tenant)
    sourcing1.refresh_aggregated_stats!
    sourcing2.refresh_aggregated_stats!
  end
  after { Apartment::Tenant.switch!("public") }

  describe "#call" do
    context "with valid sourcing ids" do
      subject(:result) { described_class.new(sourcing_ids: [ sourcing1.id, sourcing2.id ]).call }

      it "returns success" do
        expect(result[:success]).to be true
      end

      it "returns stats keyed by sourcing id" do
        expect(result[:data].keys).to contain_exactly(sourcing1.id.to_s, sourcing2.id.to_s)
      end

      it "includes sourcing basic info" do
        stats = result[:data][sourcing1.id.to_s]
        expect(stats[:sourcing_id]).to eq(sourcing1.id)
        expect(stats[:uid]).to eq(sourcing1.uid)
        expect(stats[:query]).to eq(sourcing1.query)
        expect(stats[:provider]).to eq(sourcing1.provider)
      end

      it "includes pool info" do
        pool = result[:data][sourcing1.id.to_s][:pool_info]
        expect(pool[:total_profiles]).to eq(2)
        expect(pool).to have_key(:total_pages)
        expect(pool).to have_key(:page_size)
      end

      it "includes import stats" do
        import = result[:data][sourcing1.id.to_s][:import_stats]
        expect(import[:total_imported]).to eq(1)
      end

      it "includes score distribution" do
        scores = result[:data][sourcing1.id.to_s][:score_distribution]
        expect(scores).to be_a(Hash)
      end

      it "includes meta information" do
        expect(result[:meta][:requested_count]).to eq(2)
        expect(result[:meta][:found_count]).to eq(2)
        expect(result[:meta][:computed_at]).to be_present
      end
    end

    context "with empty sourcing ids" do
      subject(:result) { described_class.new(sourcing_ids: []).call }

      it "returns error" do
        expect(result[:success]).to be false
        expect(result[:error]).to be_present
      end
    end

    context "with nonexistent sourcing ids" do
      subject(:result) { described_class.new(sourcing_ids: [ 999999 ]).call }

      it "returns error when none found" do
        expect(result[:success]).to be false
      end
    end

    context "with deleted sourcing" do
      before { sourcing1.update!(is_deleted: true) }

      subject(:result) { described_class.new(sourcing_ids: [ sourcing1.id, sourcing2.id ]).call }

      it "excludes deleted sourcings" do
        expect(result[:data].keys).to contain_exactly(sourcing2.id.to_s)
      end
    end

    context "when sourcing has no profiles" do
      let!(:empty_sourcing) { create(:sourcing, account: account, user: user, status: "done") }

      subject(:result) { described_class.new(sourcing_ids: [ empty_sourcing.id ]).call }

      it "returns empty stats" do
        stats = result[:data][empty_sourcing.id.to_s]
        expect(stats[:pool_info][:total_profiles]).to eq(0)
        expect(stats[:import_stats][:total_imported]).to eq(0)
        expect(stats[:score_distribution]).to eq({})
      end
    end
  end
end
