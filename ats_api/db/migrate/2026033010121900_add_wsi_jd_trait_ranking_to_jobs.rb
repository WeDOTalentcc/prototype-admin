# frozen_string_literal: true

class AddWsiJdTraitRankingToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :wsi_jd_trait_ranking, :jsonb, default: {} unless column_exists?(:jobs, :wsi_jd_trait_ranking)
  end
end
