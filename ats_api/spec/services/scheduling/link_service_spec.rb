# frozen_string_literal: true

require "rails_helper"

RSpec.describe Scheduling::LinkService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  subject(:service) { described_class.new(user: user) }

  describe "#create" do
    let(:params) do
      {
        subject: "Technical Interview",
        duration_minutes: 60,
        interview_type: "online",
        platform: "microsoft_teams",
        message: "Please choose a slot",
        slots: [
          { start_time: 1.day.from_now, end_time: 1.day.from_now + 1.hour },
          { start_time: 2.days.from_now, end_time: 2.days.from_now + 1.hour }
        ]
      }
    end

    it "creates a scheduling link" do
      result = service.create(params)

      expect(result.success?).to be true
      expect(result.data).to be_a(SchedulingLink)
      expect(result.data.subject).to eq("Technical Interview")
      expect(result.data.token).to be_present
    end

    it "creates associated slots" do
      result = service.create(params)

      expect(result.data.scheduling_slots.count).to eq(2)
      expect(result.data.scheduling_slots.all?(&:available?)).to be true
    end

    it "assigns the user as created_by" do
      result = service.create(params)

      expect(result.data.created_by).to eq(user)
    end

    it "sets the account" do
      result = service.create(params)

      expect(result.data.account).to eq(account)
    end
  end

  describe "#update" do
    let(:link) { create(:scheduling_link, account: account, created_by: user) }

    it "updates the link subject" do
      result = service.update(link, { subject: "Updated Subject" })

      expect(result.success?).to be true
      expect(result.data.subject).to eq("Updated Subject")
    end

    it "returns failure for non-active links" do
      link.update!(status: "booked", booked_at: Time.current)
      result = service.update(link, { subject: "Updated" })

      expect(result.success?).to be false
      expect(result.errors).to include("Link is not active")
    end

    it "replaces slots when new slots provided" do
      create(:scheduling_slot, scheduling_link: link)
      new_slots = [
        { start_time: 3.days.from_now, end_time: 3.days.from_now + 1.hour }
      ]

      result = service.update(link, { slots: new_slots })

      expect(result.success?).to be true
      expect(result.data.scheduling_slots.count).to eq(1)
    end
  end

  describe "#cancel" do
    let(:link) { create(:scheduling_link, account: account, created_by: user) }

    it "cancels the link" do
      result = service.cancel(link)

      expect(result.success?).to be true
      expect(result.data.status).to eq("cancelled")
    end

    it "returns failure for already booked links" do
      link.update!(status: "booked", booked_at: Time.current)
      result = service.cancel(link)

      expect(result.success?).to be false
      expect(result.errors).to include("Link is already booked")
    end

    it "returns failure for already cancelled links" do
      link.update!(status: "cancelled")
      result = service.cancel(link)

      expect(result.success?).to be false
      expect(result.errors).to include("Link is already cancelled")
    end
  end

  describe "#list" do
    let!(:active_link) { create(:scheduling_link, account: account, created_by: user, status: "active") }
    let!(:booked_link) { create(:scheduling_link, :booked, account: account, created_by: user) }

    it "returns all links for the user" do
      links = service.list
      expect(links.count).to eq(2)
    end

    it "filters by status" do
      links = service.list(status: "active")
      expect(links.count).to eq(1)
      expect(links.first).to eq(active_link)
    end
  end
end
