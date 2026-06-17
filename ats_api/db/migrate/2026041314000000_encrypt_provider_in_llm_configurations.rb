# frozen_string_literal: true

class EncryptProviderInLlmConfigurations < ActiveRecord::Migration[7.1]
  def up
    return unless ActiveRecord::Base.connection.table_exists?(:llm_configurations)

    add_column :llm_configurations, :encrypted_provider, :text unless column_exists?(:llm_configurations, :encrypted_provider)

    remove_index :llm_configurations, :provider if index_exists?(:llm_configurations, :provider)

    LlmConfiguration.reset_column_information
    LlmConfiguration.find_each do |config|
      raw_provider = config.read_attribute(:provider)
      next if raw_provider.blank?

      config.update_column(:encrypted_provider, LlmConfiguration.encrypt_value(raw_provider))
    end

    remove_column :llm_configurations, :provider if column_exists?(:llm_configurations, :provider)
  end

  def down
    return unless ActiveRecord::Base.connection.table_exists?(:llm_configurations)

    add_column :llm_configurations, :provider, :string, default: "gemini" unless column_exists?(:llm_configurations, :provider)

    LlmConfiguration.reset_column_information
    LlmConfiguration.find_each do |config|
      encrypted = config.read_attribute(:encrypted_provider)
      next if encrypted.blank?

      raw = LlmConfiguration.decrypt_value(encrypted)
      config.update_column(:provider, raw) if raw.present?
    end

    add_index :llm_configurations, :provider unless index_exists?(:llm_configurations, :provider)
    remove_column :llm_configurations, :encrypted_provider if column_exists?(:llm_configurations, :encrypted_provider)
  end
end
