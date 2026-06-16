class CreateCompanyProfiles < ActiveRecord::Migration[7.1]
  def change
    create_table :company_profiles, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :client_account_id
      t.string :name, limit: 255, null: false
      t.string :trading_name, limit: 255
      t.string :website, limit: 500
      t.string :logo_url, limit: 500
      t.string :cnpj, limit: 18
      t.string :industry, limit: 100
      t.string :sector, limit: 100
      t.string :company_size, limit: 50
      t.integer :founded_year
      t.text :description
      t.string :short_description, limit: 500
      t.string :headquarters_city, limit: 100
      t.string :headquarters_state, limit: 100
      t.string :headquarters_country, limit: 100, default: "Brasil"
      t.text :address
      t.string :main_phone, limit: 50
      t.string :hr_phone, limit: 50
      t.string :main_email, limit: 255
      t.string :hr_email, limit: 255
      t.string :linkedin_url, limit: 500
      t.string :glassdoor_url, limit: 500
      t.integer :employee_count
      t.string :revenue_range, limit: 100
      t.boolean :is_active, default: true
      t.boolean :is_default, default: false
      t.boolean :culture_analyzed, default: false
      t.datetime :culture_analysis_date
      t.jsonb :culture_insights, default: {}
      t.boolean :ats_history_analyzed, default: false
      t.datetime :ats_analysis_date
      t.jsonb :ats_insights, default: {}
      t.jsonb :additional_data, default: {}
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :company_profiles, :client_account_id, unique: true
    add_foreign_key :company_profiles, :client_accounts
  end
end
