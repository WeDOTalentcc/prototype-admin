class AddTrackingFieldsToDispatchMessages < ActiveRecord::Migration[7.1]
  def change
    add_column :dispatch_messages, :tracking_pixel_token, :string
    add_column :dispatch_messages, :tracking_click_token, :string
    add_column :dispatch_messages, :opened_at, :timestamp
    add_column :dispatch_messages, :clicked_at, :timestamp
    add_column :dispatch_messages, :clicked_url, :text
    add_column :dispatch_messages, :bounced_at, :timestamp
    add_column :dispatch_messages, :bounce_reason, :text

    add_index :dispatch_messages, :tracking_pixel_token
    add_index :dispatch_messages, :tracking_click_token
  end
end
