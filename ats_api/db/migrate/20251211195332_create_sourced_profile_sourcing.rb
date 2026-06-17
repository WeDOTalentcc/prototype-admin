class CreateSourcedProfileSourcing < ActiveRecord::Migration[7.1]
  def change
    create_table :sourced_profile_sourcings do |t|
      t.references :sourced_profile, null: false, foreign_key: true
      t.references :sourcing, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: false
      t.references :user, null: false, foreign_key: false

      t.string :analysis
      t.float :score
      t.boolean :is_deleted, default: false

      t.timestamps
    end
  end
end
