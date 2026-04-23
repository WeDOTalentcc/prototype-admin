# frozen_string_literal: true

require "rails_helper"

RSpec.describe MicrosoftService::TeamsMessageIngestionService do
  let(:lia_user) { instance_double(User, id: 1, email: "lia@company.com", ms_access_token: "valid-token") }
  let(:recruiter) { instance_double(User, id: 2, email: "recruiter@company.com", account_id: 10, ms_access_token: nil) }
  let(:chat_id) { "19:abc123@thread.v2" }
  let(:subscription) do
    instance_double(
      TeamsChatSubscription,
      chat_id: chat_id,
      lia_user_id: 1,
      recruiter_user_id: 2,
      tenant: "test_tenant"
    )
  end

  describe ".call" do
    before do
      allow(User).to receive(:find_by).with(id: 1).and_return(lia_user)
      allow(User).to receive(:find_by).with(id: 2).and_return(recruiter)
      allow(User).to receive(:where).with(id: 1).and_return(double(pick: "lia@company.com"))
    end

    context "when recruiter sends a message" do
      let(:teams_messages) do
        {
          "value" => [
            {
              "id" => "msg-1",
              "from" => { "user" => { "userPrincipalName" => "recruiter@company.com" } },
              "body" => { "content" => "Looks good, let's schedule an interview!" },
              "createdDateTime" => "2026-03-04T15:00:00Z"
            }
          ]
        }
      end

      before do
        allow(MicrosoftService::Api).to receive(:get).and_return(teams_messages)
        allow(Apartment::Tenant).to receive(:switch).with("test_tenant").and_yield
      end

      it "stores the recruiter message" do
        where_scope = double("where_scope")
        allow(Message).to receive(:where).and_return(where_scope)
        allow(where_scope).to receive(:where).and_return(double(exists?: false))
        allow(where_scope).to receive(:order).and_return(double(first: nil))
        allow(Message).to receive(:create!)

        described_class.call(subscription)

        expect(Message).to have_received(:create!).with(
          hash_including(
            account_id: 10,
            entity: Message::ROLE_USER,
            status: Message::STATUS_NOT_ANSWERED,
            no_reply: true
          )
        )
      end
    end

    context "when message is already stored" do
      let(:teams_messages) do
        {
          "value" => [
            {
              "id" => "msg-already-stored",
              "from" => { "user" => { "userPrincipalName" => "recruiter@company.com" } },
              "body" => { "content" => "Duplicate message" },
              "createdDateTime" => "2026-03-04T15:00:00Z"
            }
          ]
        }
      end

      before do
        allow(MicrosoftService::Api).to receive(:get).and_return(teams_messages)
        allow(Apartment::Tenant).to receive(:switch).with("test_tenant").and_yield
      end

      it "skips duplicate messages" do
        allow(Message).to receive_message_chain(:where, :where, :exists?).and_return(true)
        allow(Message).to receive(:create!)

        described_class.call(subscription)

        expect(Message).not_to have_received(:create!)
      end
    end

    context "when LIA sends a message" do
      let(:teams_messages) do
        {
          "value" => [
            {
              "id" => "msg-from-lia",
              "from" => { "user" => { "userPrincipalName" => "lia@company.com" } },
              "body" => { "content" => "AI notification" },
              "createdDateTime" => "2026-03-04T15:00:00Z"
            }
          ]
        }
      end

      before do
        allow(MicrosoftService::Api).to receive(:get).and_return(teams_messages)
      end

      it "ignores LIA messages" do
        allow(Message).to receive(:create!)

        described_class.call(subscription)

        expect(Message).not_to have_received(:create!)
      end
    end

    context "when no user has a valid token" do
      before do
        allow(lia_user).to receive(:ms_access_token).and_return(nil)
        allow(recruiter).to receive(:ms_access_token).and_return(nil)
      end

      it "does not fetch messages" do
        allow(MicrosoftService::Api).to receive(:get)

        described_class.call(subscription)

        expect(MicrosoftService::Api).not_to have_received(:get)
      end
    end

    context "when LIA has no token but recruiter does" do
      before do
        allow(lia_user).to receive(:ms_access_token).and_return(nil)
        allow(recruiter).to receive(:ms_access_token).and_return("recruiter-token")
        allow(MicrosoftService::Api).to receive(:get).and_return({ "value" => [] })
      end

      it "uses recruiter token as fallback" do
        described_class.call(subscription)

        expect(MicrosoftService::Api).to have_received(:get).with(
          anything, recruiter, anything
        )
      end
    end
  end
end
