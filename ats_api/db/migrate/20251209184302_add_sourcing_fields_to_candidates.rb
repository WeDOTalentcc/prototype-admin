class AddSourcingFieldsToCandidates < ActiveRecord::Migration[7.0]
  def change
    add_column :candidates, :external_provider, :string
    add_column :candidates, :linkedin_slug, :string
    add_column :candidates, :external_profile_data, :jsonb, default: {}

    add_index :candidates, [ :external_provider, :external_id ]
    add_index :candidates, :linkedin_slug
    add_index :candidates, :source
  end
end
