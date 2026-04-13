# frozen_string_literal: true

class CreateCandidateSourcesAndProfiles < ActiveRecord::Migration[7.1]
  def change
    create_table :candidate_sources, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :candidate_id, null: false
      t.string :source_type, null: false, limit: 50   # linkedin, referral, website, job_board, agent, import, manual
      t.string :source_detail, limit: 200              # specific board name, referrer name, etc.
      t.string :campaign_id                            # recruitment campaign that sourced
      t.string :agent_id                               # sourcing agent that found
      t.datetime :sourced_at
      t.jsonb :metadata, default: {}
      t.timestamps
    end

    add_index :candidate_sources, :candidate_id
    add_index :candidate_sources, :company_id
    add_index :candidate_sources, :source_type

    create_table :external_candidate_profiles, id: :uuid do |t|
      t.string :candidate_id, null: false
      t.string :company_id, null: false
      t.string :platform, null: false, limit: 50       # linkedin, github, portfolio, glassdoor
      t.string :profile_url, limit: 500
      t.string :external_id, limit: 200
      t.string :headline, limit: 500
      t.text :summary
      t.jsonb :profile_data, default: {}               # full scraped/enriched data
      t.datetime :last_synced_at
      t.timestamps
    end

    add_index :external_candidate_profiles, :candidate_id
    add_index :external_candidate_profiles, [:candidate_id, :platform], unique: true
  end
end
