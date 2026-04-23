class AddEnrichmentTimestampsToSourcedProfiles < ActiveRecord::Migration[7.1]
  def change
    add_column :sourced_profiles, :emails_enriched_at, :datetime
    add_column :sourced_profiles, :phones_enriched_at, :datetime
  end
end
