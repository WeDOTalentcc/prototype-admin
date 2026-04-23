class AddWsiJdBigFiveProfileInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :wsi_jd_big_five_profile, :jsonb, default: {} unless column_exists?(:jobs, :wsi_jd_big_five_profile)
  end
end
