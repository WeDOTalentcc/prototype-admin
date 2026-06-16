# frozen_string_literal: true

require "rails_helper"

RSpec.describe MessageWorker::ProcessWorker do
  let(:worker) { described_class.new }
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  before do
    allow(Apartment::Tenant).to receive(:switch!)
    allow(ActionCable.server).to receive(:broadcast)
    allow(worker).to receive(:ack!).and_return(:ack)
  end

  describe "#work - audio followup" do
    let!(:original_message) do
      create(:message,
        reference: user,
        account: account,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        content_format: "audio"
      )
    end

    let!(:system_message) do
      create(:message,
        reference: user,
        account: account,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        workspace_id: original_message.workspace_id,
        content: "Found 15 candidates"
      )
    end

    let(:audio_followup_payload) do
      {
        "original_message_id" => original_message.id,
        "user_reference_type" => "User",
        "user_reference_id" => user.id,
        "metadata" => {
          "audio_base64" => Base64.strict_encode64("fake_audio_data"),
          "audio_mime_type" => "audio/wav",
          "is_audio_followup" => true,
          "mode" => "hub"
        }
      }.to_json
    end

    it "does not create a new message" do
      allow_any_instance_of(Message).to receive(:attach_audio_from_base64).and_return(true)

      expect { worker.work(audio_followup_payload) }.not_to change(Message, :count)
    end

    it "broadcasts audio_followup type via ActionCable" do
      allow_any_instance_of(Message).to receive(:attach_audio_from_base64).and_return(true)

      worker.work(audio_followup_payload)

      expect(ActionCable.server).to have_received(:broadcast).with(
        "messages_user_#{user.id}",
        hash_including(
          type: "audio_followup",
          metadata: hash_including(
            is_audio_followup: true,
            audio_mime_type: "audio/wav"
          )
        )
      )
    end

    it "returns ack" do
      allow_any_instance_of(Message).to receive(:attach_audio_from_base64).and_return(true)

      result = worker.work(audio_followup_payload)

      expect(result).to eq(:ack)
    end
  end

  describe "#work - standard response" do
    let!(:original_message) do
      create(:message,
        reference: user,
        account: account,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED
      )
    end

    let(:standard_payload) do
      {
        "original_message_id" => original_message.id,
        "user_reference_type" => "User",
        "user_reference_id" => user.id,
        "response" => {
          "message" => "Opening all jobs",
          "has_navigation" => true,
          "generate_audio_response" => true,
          "original_content_format" => "audio",
          "navigation_actions" => [ { "action_type" => "navigate", "target" => "/user/jobs" } ]
        }
      }.to_json
    end

    it "creates a new system message" do
      expect { worker.work(standard_payload) }.to change(Message, :count).by(1)
    end

    it "marks original message as answered" do
      worker.work(standard_payload)

      original_message.reload
      expect(original_message.status).to eq(Message::STATUS_ANSWERED)
    end

    it "broadcasts the response via ActionCable" do
      worker.work(standard_payload)

      expect(ActionCable.server).to have_received(:broadcast).with(
        "messages_user_#{user.id}",
        hash_including(
          entity: Message::ROLE_SYSTEM,
          content: anything
        )
      ).at_least(:once)
    end

    it "preserves navigation metadata in new message" do
      worker.work(standard_payload)

      new_msg = Message.where(entity: Message::ROLE_SYSTEM).order(created_at: :desc).first
      expect(new_msg.metadata["has_navigation"]).to be true
      expect(new_msg.metadata["generate_audio_response"]).to be true
      expect(new_msg.metadata["original_content_format"]).to eq("audio")
    end

    context "with audio_response in response" do
      let(:payload_with_audio) do
        {
          "original_message_id" => original_message.id,
          "user_reference_type" => "User",
          "user_reference_id" => user.id,
          "response" => {
            "message" => "Here are your candidates",
            "audio_response" => {
              "audio_base64" => Base64.strict_encode64("audio_data"),
              "mime_type" => "audio/mp3"
            }
          }
        }.to_json
      end

      it "includes audio_response in broadcast" do
        allow_any_instance_of(Message).to receive(:attach_audio_from_base64).and_return(true)

        worker.work(payload_with_audio)

        expect(ActionCable.server).to have_received(:broadcast).with(
          "messages_user_#{user.id}",
          hash_including(
            audio_response: hash_including(
              audio_base64: anything,
              mime_type: "audio/mp3"
            )
          )
        )
      end
    end

    context "with audio transcription" do
      let(:payload_with_transcription) do
        {
          "original_message_id" => original_message.id,
          "user_reference_type" => "User",
          "user_reference_id" => user.id,
          "audio_transcription" => "go to jobs",
          "transcription_info" => { "model" => "gemini-2.0-flash-lite", "duration_ms" => 1200 },
          "response" => {
            "message" => "Opening jobs"
          }
        }.to_json
      end

      it "stores transcription data in original message metadata" do
        worker.work(payload_with_transcription)

        original_message.reload
        expect(original_message.metadata["audio_transcription"]).to eq("go to jobs")
        expect(original_message.metadata["transcription_info"]["model"]).to eq("gemini-2.0-flash-lite")
      end
    end
  end

  describe "#work - skips user entity messages" do
    let!(:user_message) do
      create(:message,
        reference: user,
        account: account,
        entity: Message::ROLE_USER
      )
    end

    let(:payload) do
      {
        "original_message_id" => user_message.id,
        "user_reference_type" => "User",
        "user_reference_id" => user.id,
        "response" => { "message" => "test" }
      }.to_json
    end

    it "returns ack without processing" do
      expect { worker.work(payload) }.not_to change(Message, :count)
    end
  end
end
