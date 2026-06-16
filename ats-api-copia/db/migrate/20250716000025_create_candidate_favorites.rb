# frozen_string_literal: true

class CreateCandidateFavorites < ActiveRecord::Migration[7.1]
  def change
    create_table :candidate_favorites, id: :uuid do |t|
      t.string :user_id, null: false
      t.string :candidate_id, null: false
      t.string :job_id
      t.string :company_id, null: false
      t.timestamps
    end

    add_index :candidate_favorites, [:user_id, :candidate_id], unique: true
    add_index :candidate_favorites, :company_id
    add_index :candidate_favorites, :candidate_id
  end
end
