class CreateQuestions < ActiveRecord::Migration[7.1]
  def change
    create_table :questions do |t|
      t.string :title
      t.text :description
      t.string :details
      t.integer :number_retakers
      t.integer :time
      t.bigint :evaluation_id, null: false
      t.integer :response_type
      t.integer :position
      t.boolean :deleted
      t.bigint :selective_process_id
      t.json :choices
      t.text :expected_response
      t.boolean :is_required, default: true
      t.integer :parent_question_id
      t.jsonb :value_father, default: []
      t.jsonb :extra_params, default: {}

      t.timestamps
    end

    add_index :questions, :evaluation_id
    add_index :questions, :selective_process_id
  end
end
