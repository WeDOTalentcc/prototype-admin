# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Scheduling API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:link) { create(:scheduling_link, :with_slots, account: account, created_by: user, subject: "Interview") }

  let(:base_path) { "/v1/#{account.uid}/scheduling" }

  describe "GET /v1/:account_uid/scheduling/:token" do
    it "returns the scheduling data and available slots" do
      get "#{base_path}/#{link.token}"

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body["token"]).to eq(link.token)
      expect(body["subject"]).to eq("Interview")
      expect(body["status"]).to eq("active")
      expect(body["slots"]).to be_an(Array)
      expect(body["slots"].length).to eq(3)
    end

    it "returns 404 for invalid token" do
      get "#{base_path}/invalid_token"

      expect(response).to have_http_status(:not_found)
    end

    it "returns 404 for invalid account_uid" do
      get "/v1/invalid_uid/scheduling/#{link.token}"

      expect(response).to have_http_status(:not_found)
    end

    it "returns booked status for booked link" do
      link.update!(status: "booked", booked_at: Time.current)

      get "#{base_path}/#{link.token}"

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body["status"]).to eq("booked")
    end

    it "returns expired status for expired link" do
      link.update!(status: "expired")

      get "#{base_path}/#{link.token}"

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body["status"]).to eq("expired")
    end

    it "does not require authentication" do
      get "#{base_path}/#{link.token}", headers: no_auth_headers

      expect(response).to have_http_status(:ok)
    end
  end

  describe "POST /v1/:account_uid/scheduling/:token/book" do
    let(:slot) { link.scheduling_slots.first }

    before do
      meeting = Meeting.create!(
        account: account,
        organizer: user,
        subject: "Interview",
        start_time: 1.day.from_now,
        end_time: 1.day.from_now + 1.hour,
        provider: "presential",
        sub_status: "scheduled"
      )

      calendar_event = CalendarEvent.create!(
        account: account,
        organizer: user,
        title: "Interview",
        start_time: 1.day.from_now,
        end_time: 1.day.from_now + 1.hour,
        provider: "microsoft",
        event_type: "interview",
        meeting: meeting
      )

      allow(MeetingService).to receive(:create).and_return(meeting)
      allow(CalendarService).to receive(:create).and_return(calendar_event)
      allow(Scheduling::BookingNotificationWorker).to receive(:perform_async)
    end

    it "books the selected slot" do
      post "#{base_path}/#{link.token}/book",
           params: { slot_id: slot.id }.to_json,
           headers: { "Content-Type" => "application/json" }

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body["status"]).to eq("booked")
      expect(body["subject"]).to eq("Interview")
    end

    it "marks the link as booked" do
      post "#{base_path}/#{link.token}/book",
           params: { slot_id: slot.id }.to_json,
           headers: { "Content-Type" => "application/json" }

      expect(link.reload.status).to eq("booked")
    end

    it "returns error for invalid slot" do
      post "#{base_path}/#{link.token}/book",
           params: { slot_id: 99999 }.to_json,
           headers: { "Content-Type" => "application/json" }

      expect(response).to have_http_status(:unprocessable_entity)
      body = JSON.parse(response.body)
      expect(body["errors"]).to include("Slot not found")
    end

    it "returns error for already booked link" do
      link.update!(status: "booked", booked_at: Time.current)

      post "#{base_path}/#{link.token}/book",
           params: { slot_id: slot.id }.to_json,
           headers: { "Content-Type" => "application/json" }

      expect(response).to have_http_status(:gone)
    end

    it "does not require authentication" do
      post "#{base_path}/#{link.token}/book",
           params: { slot_id: slot.id }.to_json,
           headers: { "Content-Type" => "application/json" }

      expect(response).to have_http_status(:ok)
    end
  end
end
