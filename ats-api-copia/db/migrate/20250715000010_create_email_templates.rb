class CreateEmailTemplates < ActiveRecord::Migration[7.1]
  def change
    create_table :email_templates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :company_id, limit: 255
      t.string :name, limit: 255
      t.string :subject, limit: 500
      t.text :body_html
      t.text :body_text
      t.string :category, limit: 50
      t.string :channel, limit: 20, default: "email"
      t.string :situation, limit: 50
      t.string :trigger_type, limit: 20, default: "manual"
      t.jsonb :used_in, default: []
      t.string :priority, limit: 10, default: "medium"
      t.jsonb :variables, default: {}
      t.boolean :is_active, default: true
      t.boolean :is_system_template, default: false
      t.string :visibility, limit: 20, default: "all"
      t.uuid :origin_template_id
      t.integer :version, default: 1
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :email_templates, :company_id
    add_index :email_templates, :category
    add_index :email_templates, :channel
    add_index :email_templates, :is_active
    add_index :email_templates, :is_system_template
    add_index :email_templates, [:company_id, :channel]
  end
end
