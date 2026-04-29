# frozen_string_literal: true

class AddProviderToDispatches < ActiveRecord::Migration[7.1]
  def change
    add_column :dispatches, :provider, :string, default: 'mailgun', null: false unless column_exists?(:dispatches, :provider)
    add_index :dispatches, :provider unless index_exists?(:dispatches, :provider)
  end
end
