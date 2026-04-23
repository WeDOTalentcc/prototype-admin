class CreateEmailTemplate < ActiveRecord::Migration[7.1]
  def change
    unless ActiveRecord::Base.connection.table_exists? 'email_templates'
      create_table :email_templates do |t|
        t.string :name
        t.text :content
        t.string :subject
        t.string :category
        t.references :account, null: false, foreign_key: false
        t.references :user, null: false, foreign_key: false
        t.boolean :is_deleted, default: false
        t.integer :category_id, null: false
        t.timestamps
      end
    end
  end
end
