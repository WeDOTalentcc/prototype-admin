# frozen_string_literal: true

class AddAddressToBusinesses < ActiveRecord::Migration[7.1]
  def change
    add_column :businesses, :address, :string unless column_exists?(:businesses, :address)
  end
end
