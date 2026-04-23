class AddCultureFieldsInBusiness < ActiveRecord::Migration[7.1]
  def change
    add_column :businesses, :mission, :text, null: true if !column_exists?(:businesses, :mission)
    add_column :businesses, :vision, :text, null: true if !column_exists?(:businesses, :vision)
    add_column :businesses, :culture_values, :jsonb, default: [], null: false if !column_exists?(:businesses, :culture_values)
    add_column :businesses, :soft_skills, :jsonb, default: [], null: false if !column_exists?(:businesses, :soft_skills)
    add_column :businesses, :work_model, :string, null: true if !column_exists?(:businesses, :work_model)
    add_column :businesses, :growth_opportunities, :text, null: true if !column_exists?(:businesses, :growth_opportunities)
    add_column :businesses, :team_dynamics, :text, null: true if !column_exists?(:businesses, :team_dynamics)
    add_column :businesses, :leader_style, :text, null: true if !column_exists?(:businesses, :leader_style)
    add_column :businesses, :evp_highlights, :text, null: true if !column_exists?(:businesses, :evp_highlights)
    add_column :businesses, :diversity_and_inclusion, :text, null: true if !column_exists?(:businesses, :diversity_and_inclusion)
    add_column :businesses, :sustainability, :text, null: true if !column_exists?(:businesses, :sustainability)
    add_column :businesses, :social_impact, :text, null: true if !column_exists?(:businesses, :social_impact)
  end
end
