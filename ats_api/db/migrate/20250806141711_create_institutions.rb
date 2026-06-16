class CreateInstitutions < ActiveRecord::Migration[7.1]
 def change
    create_table :institutions do |t|
      t.string :name
      t.boolean :approved, default: false
      t.string :reference_type
      t.integer :reference_id
      t.timestamps
      t.integer :account_id, array: true, default: []
    end

    add_index :institutions, :reference_id
    add_index :institutions, :account_id, using: :gin
  end
end
