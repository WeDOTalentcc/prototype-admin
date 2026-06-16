# frozen_string_literal: true

class AddLinkedinEnrichmentToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :linkedin_enriched_at, :datetime
    add_index :candidates, :linkedin_enriched_at
  end
end
