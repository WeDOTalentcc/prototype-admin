# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ActivityLogSerializer, type: :serializer do
  let(:user) { create(:user, name: 'John Doe', email: 'john@example.com') }
  let(:account) { create(:account, name: 'Test Account') }
  let(:job) { create(:job, account: account) }
  let(:changeset) do
    {
      'title' => { 'from' => 'Old Title', 'to' => 'New Title' },
      'description' => { 'from' => 'Old Description', 'to' => 'New Description' }
    }
  end
  let(:activity_log) do
    create(:activity_log,
           reference_type: 'Job',
           reference_id: job.id,
           action: 'update',
           changeset: changeset,
           user: user,
           account: account,
           ip_address: '192.168.1.1',
           created_at: Time.zone.parse('2023-01-01 10:00:00'),
           updated_at: Time.zone.parse('2023-01-01 10:00:00'))
  end

  describe '.new' do
    let(:serializer) { described_class.new(activity_log) }
    let(:serialized_data) { serializer.serializable_hash[:data] }

    it 'includes all required attributes' do
      expect(serialized_data[:attributes]).to include(
        :id,
        :action,
        :user_id,
        :account_id,
        :created_at,
        :updated_at,
        :reference_type,
        :reference_id,
        :ip_address,
        :rolled_back_from_id,
        :changeset
      )
    end

    it 'serializes basic attributes correctly' do
      attributes = serialized_data[:attributes]

      expect(attributes[:id]).to eq(activity_log.id)
      expect(attributes[:action]).to eq('update')
      expect(attributes[:reference_type]).to eq('Job')
      expect(attributes[:reference_id]).to eq(job.id)
      expect(attributes[:user_id]).to eq(user.id)
      expect(attributes[:account_id]).to eq(account.id)
      expect(attributes[:ip_address]).to eq('192.168.1.1')
    end

    it 'includes changeset data' do
      attributes = serialized_data[:attributes]

      expect(attributes[:changeset]).to eq(changeset)
      expect(attributes[:changeset]['title']['from']).to eq('Old Title')
      expect(attributes[:changeset]['title']['to']).to eq('New Title')
    end

    it 'handles nil values correctly' do
      activity_log_without_user = create(:activity_log, user: nil, account: nil)
      serializer = described_class.new(activity_log_without_user)
      attributes = serializer.serializable_hash[:data][:attributes]

      expect(attributes[:user_id]).to be_nil
      expect(attributes[:account_id]).to be_nil
    end

    it 'includes timestamps' do
      attributes = serialized_data[:attributes]

      expect(attributes[:created_at]).to be_present
      expect(attributes[:updated_at]).to be_present
    end
  end

  describe 'with collection' do
    let(:activity_logs) { create_list(:activity_log, 3, user: user, account: account) }
    let(:serializer) { described_class.new(activity_logs) }
    let(:serialized_data) { serializer.serializable_hash[:data] }

    it 'serializes multiple activity logs' do
      expect(serialized_data).to be_an(Array)
      expect(serialized_data.length).to eq(3)
    end

    it 'includes correct attributes for each item' do
      serialized_data.each do |item|
        expect(item[:attributes]).to include(
          :id,
          :action,
          :reference_type,
          :changeset
        )
      end
    end
  end

  describe 'with rollback activity log' do
    let(:rollback_log) do
      create(:activity_log,
             action: 'rollback',
             rolled_back_from_id: 123,
             user: user,
             account: account)
    end
    let(:serializer) { described_class.new(rollback_log) }
    let(:serialized_data) { serializer.serializable_hash[:data] }

    it 'includes rollback-specific attributes' do
      attributes = serialized_data[:attributes]

      expect(attributes[:action]).to eq('rollback')
      expect(attributes[:rolled_back_from_id]).to eq(123)
    end
  end

  describe 'JSONAPI compliance' do
    let(:serializer) { described_class.new(activity_log) }
    let(:serialized_hash) { serializer.serializable_hash }

    it 'follows JSONAPI structure' do
      expect(serialized_hash).to have_key(:data)
      expect(serialized_hash[:data]).to have_key(:id)
      expect(serialized_hash[:data]).to have_key(:type)
      expect(serialized_hash[:data]).to have_key(:attributes)
    end

    it 'uses correct type' do
      expect(serialized_hash[:data][:type]).to eq(:activity_log)
    end

    it 'uses string ID' do
      expect(serialized_hash[:data][:id]).to eq(activity_log.id.to_s)
    end
  end
end
