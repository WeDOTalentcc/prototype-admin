# frozen_string_literal: true

class AddLocationToMeetings < ActiveRecord::Migration[7.1]
  def change
    add_column :meetings, :location, :string unless column_exists?(:meetings, :location)
  end
end
