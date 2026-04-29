class CreateJobFieldTemplates < ActiveRecord::Migration[7.1]
  def change
    create_table :job_field_templates do |t|
      t.string :name, null: false
      t.references :account, null: false, foreign_key: false
      t.boolean :is_default, default: false, null: false
      t.jsonb :fields, default: [], null: false

      t.timestamps
    end

    add_index :job_field_templates, [ :account_id, :is_default ],
              name: 'index_job_field_templates_on_account_and_default'
  end
end
