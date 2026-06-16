# frozen_string_literal: true

require "rails_helper"

RSpec.describe V1::Webhooks::MicrosoftTeams::TeamsWebhookController, type: :controller do
  describe "POST #create" do
    context "when receiving a validation request" do
      it "returns the validation token as plain text" do
        post :create, params: { validationToken: "test-token-123" }

        expect(response).to have_http_status(:ok)
        expect(response.body).to eq("test-token-123")
      end
    end

    context "when receiving empty notifications" do
      it "returns ok" do
        post :create, params: {}

        expect(response).to have_http_status(:ok)
      end
    end

    context "when receiving a chat message notification" do
      let(:chat_id) { "19:abc123@thread.v2" }
      let(:tenant) { "test_tenant" }
      let(:subscription_id) { "sub-123" }

      before do
        allow(Account).to receive(:pluck).with(:tenant).and_return([ tenant ])
        allow(Apartment::Tenant).to receive(:switch).with(tenant).and_yield
        allow(ActiveRecord::Base.connection).to receive(:table_exists?)
          .with(:teams_chat_subscriptions).and_return(true)
        allow(TeamsChatSubscription).to receive(:exists?)
          .with(chat_id: chat_id, status: "active").and_return(true)
        allow(Microsoft::TeamsMessageIngestionJob).to receive(:perform_async)
        allow(Rails.cache).to receive(:read).and_return(nil)
        allow(Rails.cache).to receive(:write)
      end

      it "enqueues the ingestion job" do
        post :create, params: {
          value: [ {
            subscriptionId: subscription_id,
            resource: "chats('#{chat_id}')/messages('msg-1')",
            resourceData: { id: "msg-1" }
          } ]
        }

        expect(Microsoft::TeamsMessageIngestionJob).to have_received(:perform_async)
          .with(chat_id, tenant, "msg-1")
        expect(response).to have_http_status(:accepted)
      end

      it "extracts chat_id from slash-based resource format" do
        post :create, params: {
          value: [ {
            subscriptionId: subscription_id,
            resource: "chats/#{chat_id}/messages",
            resourceData: { id: "msg-2" }
          } ]
        }

        expect(Microsoft::TeamsMessageIngestionJob).to have_received(:perform_async)
          .with(chat_id, tenant, "msg-2")
      end

      it "caches the tenant for subsequent lookups" do
        post :create, params: {
          value: [ {
            subscriptionId: subscription_id,
            resource: "chats('#{chat_id}')/messages('msg-1')",
            resourceData: { id: "msg-1" }
          } ]
        }

        expect(Rails.cache).to have_received(:write)
          .with("teams_sub_tenant:#{subscription_id}", tenant, expires_in: 1.hour)
      end

      it "uses cached tenant without searching" do
        allow(Rails.cache).to receive(:read)
          .with("teams_sub_tenant:#{subscription_id}").and_return(tenant)

        post :create, params: {
          value: [ {
            subscriptionId: subscription_id,
            resource: "chats('#{chat_id}')/messages('msg-1')",
            resourceData: { id: "msg-1" }
          } ]
        }

        expect(TeamsChatSubscription).not_to have_received(:exists?)
        expect(Microsoft::TeamsMessageIngestionJob).to have_received(:perform_async)
      end
    end

    context "when no active subscription exists for chat" do
      it "does not enqueue the ingestion job" do
        allow(Account).to receive(:pluck).with(:tenant).and_return([ "t1" ])
        allow(Apartment::Tenant).to receive(:switch).with("t1").and_yield
        allow(ActiveRecord::Base.connection).to receive(:table_exists?)
          .with(:teams_chat_subscriptions).and_return(true)
        allow(TeamsChatSubscription).to receive(:exists?).and_return(false)
        allow(Microsoft::TeamsMessageIngestionJob).to receive(:perform_async)
        allow(Rails.cache).to receive(:read).and_return(nil)

        post :create, params: {
          value: [ {
            subscriptionId: "sub-x",
            resource: "chats('19:unknown@thread.v2')/messages('msg-1')",
            resourceData: { id: "msg-1" }
          } ]
        }

        expect(Microsoft::TeamsMessageIngestionJob).not_to have_received(:perform_async)
      end
    end

    context "when receiving a lifecycle event" do
      let(:tenant) { "test_tenant" }

      it "triggers subscription renewal" do
        record = instance_double(TeamsChatSubscription, lia_user_id: 1, chat_id: "chat-1")
        lia_user = instance_double(User, id: 1)

        allow(Account).to receive(:pluck).with(:tenant).and_return([ tenant ])
        allow(Apartment::Tenant).to receive(:switch).with(tenant).and_yield
        allow(ActiveRecord::Base.connection).to receive(:table_exists?)
          .with(:teams_chat_subscriptions).and_return(true)
        allow(TeamsChatSubscription).to receive(:exists?)
          .with(subscription_id: "sub-expired").and_return(true)
        allow(TeamsChatSubscription).to receive(:find_by)
          .with(subscription_id: "sub-expired").and_return(record)
        allow(User).to receive(:find_by).with(id: 1).and_return(lia_user)
        allow(MicrosoftService::TeamsSubscriptionService).to receive(:create_or_renew)
        allow(Rails.cache).to receive(:read).and_return(nil)
        allow(Rails.cache).to receive(:write)

        post :create, params: {
          value: [ {
            lifecycleEvent: "reauthorizationRequired",
            subscriptionId: "sub-expired"
          } ]
        }

        expect(MicrosoftService::TeamsSubscriptionService).to have_received(:create_or_renew)
          .with(lia_user, "chat-1")
        expect(response).to have_http_status(:accepted)
      end
    end
  end
end
