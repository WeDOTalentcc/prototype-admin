# frozen_string_literal: true

require 'rails_helper'

RSpec.describe MessageService::ConnectionPool do
  describe '.connection' do
    it 'returns the same connection instance on multiple calls' do
      conn1 = described_class.connection
      conn2 = described_class.connection
      expect(conn1).to be(conn2)
    end
  end

  describe '.channel' do
    it 'returns a new channel from the shared connection' do
      channel = described_class.channel
      expect(channel).to be_a(Bunny::Channel)
      expect(channel.connection).to be(described_class.connection)
      channel.close
    end
  end
end
