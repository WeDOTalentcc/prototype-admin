class AddUiFieldsToAgentNotifications < ActiveRecord::Migration[7.1]
  def change
    add_column :agent_notifications, :title, :string unless column_exists?(:agent_notifications, :title)
    add_column :agent_notifications, :category, :string unless column_exists?(:agent_notifications, :category)
    add_column :agent_notifications, :priority, :string, default: "normal" unless column_exists?(:agent_notifications, :priority)
    add_column :agent_notifications, :proactive_type, :string unless column_exists?(:agent_notifications, :proactive_type)
    add_column :agent_notifications, :action_url, :string unless column_exists?(:agent_notifications, :action_url)
    add_column :agent_notifications, :action_label, :string unless column_exists?(:agent_notifications, :action_label)

    add_index :agent_notifications, [ :user_id, :read_at ], name: "index_agent_notifications_on_user_id_and_read_at" unless index_exists?(:agent_notifications, [ :user_id, :read_at ])
    add_index :agent_notifications, :category unless index_exists?(:agent_notifications, :category)
  end
end
