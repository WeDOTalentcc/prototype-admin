class AddChannelsInSchedulingLink < ActiveRecord::Migration[7.1]
  def change
    add_column :scheduling_links, :channels, :string, array: true, default: [] unless column_exists?(:scheduling_links, :channels)
  end
end
