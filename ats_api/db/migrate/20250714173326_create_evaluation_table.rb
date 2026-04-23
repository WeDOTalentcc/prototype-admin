class CreateEvaluationTable < ActiveRecord::Migration[7.1]
  def change
    create_table :evaluations do |t|
      t.string :name
      t.references :job, null: true, foreign_key: true
      t.references :selective_process, null: true, foreign_key: true
      t.references :user, null: true, foreign_key: true
      t.references :account, null: false, foreign_key: true
      t.boolean :status, default: true
      t.integer :position, default: 0
      t.string :sub_status, default: nil
      t.text :description, default: nil
      t.boolean :is_main, default: false
      t.integer :time, default: 90
      t.string :uid
      t.boolean :is_chatbot, default: false
      t.boolean :ai_enabled, default: false
      t.timestamps
    end
    add_index :evaluations, :uid
  end
end
