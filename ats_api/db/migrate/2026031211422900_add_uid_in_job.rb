class AddUidInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :uid, :string, null: false, default: "" if !column_exists?(:jobs, :uid)
    add_column :jobs, :is_published, :boolean, default: false, null: false if !column_exists?(:jobs, :is_published)
    add_column :jobs, :slug, :string, null: false, default: "" if !column_exists?(:jobs, :slug)

    add_column :accounts, :slug, :string, null: false, default: "" if !column_exists?(:accounts, :slug)
  end
end
