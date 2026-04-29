class AddDiversityLgpdTwinFieldsToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :pcd,             :boolean,  default: false, null: false
    add_column :candidates, :ethnicity,       :integer
    add_column :candidates, :lgbtqia,         :boolean,  default: false, null: false
    add_column :candidates, :neurodivergent,  :boolean,  default: false, null: false
    add_column :candidates, :is_hidden,       :boolean,  default: false, null: false
    add_column :candidates, :lgpd_expires_at, :datetime
    add_column :candidates, :is_twin,         :boolean,  default: false, null: false
    add_column :candidates, :twin_source_id,  :bigint

    add_index :candidates, :pcd
    add_index :candidates, :ethnicity
    add_index :candidates, :is_hidden
    add_index :candidates, :is_twin
    add_index :candidates, :twin_source_id
    add_index :candidates, :lgpd_expires_at
  end
end
