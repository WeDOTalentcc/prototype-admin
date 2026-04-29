class CreateFeedback < ActiveRecord::Migration[7.1]
  def change
    create_table :feedbacks do |t|
      t.string :title
      t.text :description
      t.string :name
      t.text :additional_text
      t.boolean :is_deleted, default: false
      t.references :job, null: false, foreign_key: true
      t.references :selective_process, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: { to_table: 'public.accounts' }
      t.timestamps
    end
  end
end
