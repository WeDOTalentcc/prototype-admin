# frozen_string_literal: true

class AddSchedulingFieldsToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :sub_status, :string unless column_exists?(:applies, :sub_status)
  end
end
