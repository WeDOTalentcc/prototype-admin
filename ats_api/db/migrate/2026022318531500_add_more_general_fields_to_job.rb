class AddMoreGeneralFieldsToJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :priority, :integer unless column_exists?(:jobs, :priority)
    add_column :jobs, :urgency_level, :integer unless column_exists?(:jobs, :urgency_level)
    add_column :jobs, :main_pcd_category, :integer unless column_exists?(:jobs, :main_pcd_category)
    add_column :jobs, :secondary_pcd_category, :integer unless column_exists?(:jobs, :secondary_pcd_category)
    add_column :jobs, :pcd_description, :string unless column_exists?(:jobs, :pcd_description)
    add_column :jobs, :required_pcd_files, :boolean, default: false unless column_exists?(:jobs, :required_pcd_documents)
    add_column :jobs, :pcd_files_description, :string unless column_exists?(:jobs, :pcd_files_description)
    add_column :jobs, :sector, :string unless column_exists?(:jobs, :sector)
    add_column :jobs, :segment, :string unless column_exists?(:jobs, :segment)
    add_column :jobs, :target_audience, :string unless column_exists?(:jobs, :target_audience)
    add_column :jobs, :has_linkedin_post, :boolean, default: false unless column_exists?(:jobs, :has_linkedin_post)
    add_column :jobs, :has_website_post, :boolean, default: false unless column_exists?(:jobs, :has_website_post)
    add_column :jobs, :has_indeed_post, :boolean, default: false unless column_exists?(:jobs, :has_indeed_post)
    add_column :jobs, :confidential_type, :integer unless column_exists?(:jobs, :confidential_type)
    add_column :jobs, :confidential_company_name, :string unless column_exists?(:jobs, :confidential_company_name)
    add_column :jobs, :is_screening_active, :boolean, default: false unless column_exists?(:jobs, :is_screening_active)
  end
end
