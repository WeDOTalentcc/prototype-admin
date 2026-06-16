# frozen_string_literal: true

require "rails_helper"

RSpec.describe CalendarEvent, "post-interview dispatch callbacks" do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account) }
  let(:candidate) { create(:candidate, account: account, email: "test@example.com") }
  let(:apply) { create(:apply, candidate: candidate, job: job, account: account) }

  before do
    Apartment::Tenant.switch!(account.tenant)
  end

  describe "after_create_commit" do
    let!(:template) { create(:email_template, :post_interview, account: account, user: user) }

    it "schedules post-interview dispatch for interview events" do
      expect {
        create(:calendar_event,
               organizer: user,
               account: account,
               event_type: "interview",
               job: job,
               apply: apply)
      }.to change(Dispatch, :count).by(1)
    end

    it "does not schedule dispatch for non-interview events" do
      expect {
        create(:calendar_event,
               organizer: user,
               account: account,
               event_type: "generic",
               job: job)
      }.not_to change(Dispatch, :count)
    end
  end

  describe "after_update_commit (reschedule)" do
    let!(:template) { create(:email_template, :post_interview, account: account, user: user) }
    let!(:event) do
      create(:calendar_event,
             organizer: user,
             account: account,
             event_type: "interview",
             job: job,
             apply: apply,
             start_time: 1.day.from_now,
             end_time: 1.day.from_now + 1.hour)
    end

    it "cancels old dispatch and creates new one when end_time changes" do
      old_dispatch = Dispatch.last
      expect(old_dispatch.status).to eq("pending")

      event.update!(end_time: 2.days.from_now + 1.hour, start_time: 2.days.from_now)

      expect(old_dispatch.reload.status).to eq("failed")
      expect(Dispatch.pending.count).to eq(1)

      new_dispatch = Dispatch.pending.last
      expect(new_dispatch.scheduled_for).to be_within(1.minute).of(event.end_time + template.delay_hours.hours)
    end
  end

  describe "after_update_commit (cancel)" do
    let!(:template) { create(:email_template, :post_interview, account: account, user: user) }
    let!(:event) do
      create(:calendar_event,
             organizer: user,
             account: account,
             event_type: "interview",
             job: job,
             apply: apply)
    end

    it "cancels pending dispatch when event is cancelled" do
      dispatch = Dispatch.last
      expect(dispatch.status).to eq("pending")

      event.cancel!

      expect(dispatch.reload.status).to eq("failed")
    end

    it "cancels pending dispatch when event is deleted" do
      dispatch = Dispatch.last
      expect(dispatch.status).to eq("pending")

      event.soft_delete!

      expect(dispatch.reload.status).to eq("failed")
    end
  end
end
