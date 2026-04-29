class CreateAnswers < ActiveRecord::Migration[7.1]
  def change
    return if table_exists?(:answers)

    create_table :answers do |t|
      t.string  :title
      t.bigint  :question_id
      t.bigint  :evaluation_id
      t.bigint  :candidate_id
      t.bigint  :job_id
      t.integer :time
      t.text    :description
      t.string  :detail
      t.bigint  :apply_id
      t.bigint  :user_id
      t.json    :choices
      t.integer :time_taken
      t.string  :represent_field
      t.text    :comments_response
      t.integer :reference_id
      t.string  :reference_type
      t.integer :account_id
      t.timestamps
    end

    add_index :answers, :question_id
    add_index :answers, :evaluation_id
    add_index :answers, :candidate_id
    add_index :answers, :job_id
    add_index :answers, :apply_id
    add_index :answers, :user_id
    add_index :answers, :account_id
    add_index :answers, [ :reference_type, :reference_id ]
  end
end
