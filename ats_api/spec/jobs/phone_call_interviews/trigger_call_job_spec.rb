# frozen_string_literal: true

RSpec.describe PhoneCallInterviews::TriggerCallJob, type: :job do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:evaluation) { create(:evaluation, account: account) }
  let(:candidate) { create(:candidate, account: account, mobile_phone: "+5511999999999") }
  let(:job_record) { create(:job, account: account) }

  let(:ec) do
    create(:evaluation_candidate,
      account: account,
      user: user,
      evaluation: evaluation,
      candidate: candidate,
      job: job_record,
      evaluation_type: :phone_call,
      phone_call_status: "scheduled",
      scheduled_at: Time.current
    )
  end

  before { Apartment::Tenant.switch!(account.tenant) }

  it "creates an interview session" do
    stub_request(:post, "http://localhost:8001/api/v1/phone-call/initiate")
      .to_return(status: 200, body: {}.to_json)

    expect { described_class.new.perform(ec.id, account.id) }
      .to change(InterviewSession, :count).by(1)
  end

  it "updates evaluation candidate status to calling" do
    stub_request(:post, "http://localhost:8001/api/v1/phone-call/initiate")
      .to_return(status: 200, body: {}.to_json)

    described_class.new.perform(ec.id, account.id)
    expect(ec.reload.phone_call_status).to eq("calling")
  end

  it "sets interview_type to phone on the session" do
    stub_request(:post, "http://localhost:8001/api/v1/phone-call/initiate")
      .to_return(status: 200, body: {}.to_json)

    described_class.new.perform(ec.id, account.id)
    expect(ec.reload.interview_session.interview_type).to eq("phone")
  end

  context "when evaluation candidate is not scheduled" do
    let(:ec) do
      create(:evaluation_candidate,
        account: account,
        user: user,
        evaluation: evaluation,
        candidate: candidate,
        job: job_record,
        evaluation_type: :phone_call,
        phone_call_status: "pending_schedule"
      )
    end

    it "does not trigger the call" do
      described_class.new.perform(ec.id, account.id)
      expect(ec.reload.phone_call_status).to eq("pending_schedule")
    end
  end

  context "when python service returns error" do
    it "marks status as failed" do
      stub_request(:post, "http://localhost:8001/api/v1/phone-call/initiate")
        .to_return(status: 500, body: { error: "Internal error" }.to_json)

      expect { described_class.new.perform(ec.id, account.id) }.to raise_error(StandardError)
      expect(ec.reload.phone_call_status).to eq("failed")
    end
  end

  context "when account not found" do
    it "does not raise" do
      expect { described_class.new.perform(ec.id, 999_999) }.not_to raise_error
    end
  end
end
