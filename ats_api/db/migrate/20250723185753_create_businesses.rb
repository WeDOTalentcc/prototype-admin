class CreateBusinesses < ActiveRecord::Migration[7.1]
  def change
    create_table :businesses do |t|
      t.string :name, null: false
      t.string :cnpj
      t.string :email
      t.string :phone
      t.string :website
      t.string :industry
      t.string :size
      t.string :linkedin
      t.text :about
      t.boolean :is_active, default: true
      t.references :account, null: false, foreign_key: { to_table: 'public.accounts' }

      t.timestamps
    end
  end
end
