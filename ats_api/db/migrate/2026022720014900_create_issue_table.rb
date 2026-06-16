class CreateIssueTable < ActiveRecord::Migration[7.1]
  def change
    create_table :issues do |t|
      t.text :text, null: false, default: ""
      t.integer :type, null: false, default: 0
      t.integer :status, null: false, default: 0
      t.references :account, null: false, foreign_key: false
      t.references :candidate, null: false, foreign_key: true
      t.references :evaluation, null: false, foreign_key: true
      t.references :evaluation_candidate, null: false, foreign_key: true
      t.references :question, null: true, foreign_key: true
      t.string :reference_type, null: false, default: ""
      t.integer :reference_id, null: false, default: 0
      t.references :job, null: true, foreign_key: true
      t.timestamps
    end
  end
end
