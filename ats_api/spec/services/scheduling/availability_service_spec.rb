# frozen_string_literal: true

require "rails_helper"

RSpec.describe Scheduling::AvailabilityService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account, email: "recruiter@test.com") }
  let!(:settings) { create(:scheduling_setting, user: user, account: account) }

  subject(:service) { described_class.new(user: user) }

  describe "#available_slots" do
    let(:target_date) { Date.current + 1.day }

    before do
      allow(MicrosoftService::Api).to receive(:post).and_return(
        {
          "value" => [
            {
              "scheduleItems" => [
                {
                  "start" => { "dateTime" => "#{target_date}T13:00:00Z" },
                  "end" => { "dateTime" => "#{target_date}T14:00:00Z" }
                }
              ]
            }
          ]
        }
      )
    end

    it "returns slots with status field" do
      result = service.available_slots(date: target_date)

      expect(result).to have_key(:slots)
      expect(result).to have_key(:busy_periods)
      expect(result[:slots]).to be_an(Array)
      expect(result[:slots]).not_to be_empty

      result[:slots].each do |slot|
        expect(slot).to have_key(:start_time)
        expect(slot).to have_key(:end_time)
        expect(slot[:status]).to be_in(%w[available busy past])
      end
    end

    it "marks slots overlapping busy periods as busy" do
      result = service.available_slots(date: target_date)

      busy_start = Time.parse("#{target_date}T13:00:00Z")
      busy_end = Time.parse("#{target_date}T14:00:00Z")

      result[:slots].each do |slot|
        slot_start = Time.parse(slot[:start_time])
        slot_end = Time.parse(slot[:end_time])
        overlaps = slot_start < busy_end && slot_end > busy_start
        expect(slot[:status]).to eq("busy") if overlaps
      end
    end

    it "returns busy_periods from Microsoft calendar" do
      result = service.available_slots(date: target_date)

      expect(result[:busy_periods]).to be_an(Array)
      expect(result[:busy_periods].length).to eq(1)
      expect(result[:busy_periods].first).to have_key(:start_time)
      expect(result[:busy_periods].first).to have_key(:end_time)
    end

    it "caches the result" do
      service.available_slots(date: target_date)

      cached = CachedAvailability.find_by(user: user, date: target_date)
      expect(cached).to be_present
      expect(cached.fresh?).to be true
      expect(cached.all_slots[:slots]).to be_an(Array)
      expect(cached.all_slots[:busy_periods]).to be_an(Array)
    end

    it "uses cached data when fresh" do
      cached_slots = [ { "start_time" => "2025-01-01T09:00:00-03:00", "end_time" => "2025-01-01T10:00:00-03:00", "status" => "available" } ]
      cached_busy = [ { "start_time" => "2025-01-01T13:00:00Z", "end_time" => "2025-01-01T14:00:00Z" } ]
      create(:cached_availability,
        user: user,
        date: target_date,
        slots_data: { "slots" => cached_slots, "busy_periods" => cached_busy },
        fetched_at: Time.current
      )

      result = service.available_slots(date: target_date)
      expect(result[:slots]).to eq(cached_slots)
      expect(result[:busy_periods]).to eq(cached_busy)
      expect(MicrosoftService::Api).not_to have_received(:post)
    end

    it "returns empty for dates beyond lookahead" do
      far_date = Date.current + 30.days
      result = service.available_slots(date: far_date)
      expect(result[:slots]).to eq([])
      expect(result[:busy_periods]).to eq([])
    end

    context "when Microsoft API fails" do
      before do
        allow(MicrosoftService::Api).to receive(:post).and_raise(StandardError, "API error")
      end

      it "returns slots without busy period filtering" do
        result = service.available_slots(date: target_date)
        expect(result[:slots]).to be_an(Array)
        expect(result[:slots]).to all(include(status: "available").or(include(status: "past")))
      end
    end
  end

  describe "#available_slots_for_range" do
    let(:start_date) { Date.current + 1.day }
    let(:end_date) { Date.current + 2.days }

    before do
      allow(MicrosoftService::Api).to receive(:post).and_return(
        { "value" => [ { "scheduleItems" => [] } ] }
      )
    end

    it "returns slots for multiple days" do
      result = service.available_slots_for_range(start_date: start_date, end_date: end_date)

      expect(result).to have_key(:slots)
      expect(result).to have_key(:busy_periods)
      expect(result[:slots]).to be_an(Array)

      dates = result[:slots].map { |s| s[:date] }.uniq
      expect(dates.length).to be >= 1
    end
  end
end
