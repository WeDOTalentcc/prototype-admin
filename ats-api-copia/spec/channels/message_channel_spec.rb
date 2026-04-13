# spec/channels/message_channel_spec.rb
require 'rails_helper'

RSpec.describe MessageChannel, type: :channel do
  let(:user) { create(:user) }

  before do
    # Isso vai simular a conexão com o usuário logado
    stub_connection current_user: user
  end

  it "successfully subscribes and streams from the correct stream" do
    subscribe
    expect(subscription).to be_confirmed
    expect(subscription).to have_stream_from("messages_user_#{user.id}")
  end
end
