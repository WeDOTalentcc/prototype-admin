class CreateSourcedProfiles < ActiveRecord::Migration[7.0]
  def change
    create_table :sourced_profiles do |t|
      t.references :sourcing, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: true

      # Identificação única
      t.string :uid, null: false
      t.string :provider, default: 'pearch'
      t.string :external_id, null: false # docid do provider
      t.string :linkedin_slug
      t.string :linkedin_url

      # Dados pessoais básicos
      t.string :name
      t.string :first_name
      t.string :middle_name
      t.string :last_name
      t.string :email
      t.string :phone
      t.string :cpf
      t.date :date_birth

      # Apresentação
      t.string :title
      t.text :summary
      t.string :picture_url

      # Dados demográficos
      t.integer :gender # seguindo padrão do Candidate
      t.integer :marital_status
      t.integer :estimated_age

      # Localização
      t.string :location
      t.string :city
      t.string :state
      t.string :country
      t.string :address
      t.string :zip_code

      # Trabalho remoto e mobilidade
      t.boolean :remote_work
      t.boolean :mobility

      # Profissional
      t.string :current_company
      t.string :current_title
      t.string :role_name
      t.string :position_level
      t.integer :total_experience_years

      # Expectativas salariais
      t.string :currency
      t.decimal :clt_expectation, precision: 10, scale: 2
      t.decimal :pj_expectation, precision: 10, scale: 2
      t.decimal :freelance_expectation, precision: 10, scale: 2

      # Classificação
      t.boolean :is_decision_maker, default: false
      t.boolean :is_top_universities, default: false

      # Arrays de dados estruturados
      t.jsonb :expertise, default: []
      t.jsonb :languages_data, default: []
      t.jsonb :skills_data, default: []

      # Informações de contato
      t.boolean :has_emails, default: false
      t.boolean :has_phone_numbers, default: false

      # Social/Profissional
      t.integer :followers_count
      t.integer :connections_count

      # Dados completos do perfil
      t.jsonb :profile_data, default: {}
      t.jsonb :experiences_data, default: []
      t.jsonb :educations_data, default: []
      t.jsonb :certifications_data, default: []
      t.jsonb :awards_data, default: []

      # Score e insights da busca
      t.integer :score
      t.jsonb :insights, default: {}

      # Pipeline de recrutamento
      t.string :status, default: 'new' # new, viewed, interested, contacted, rejected, hired
      t.integer :rating # 1-5
      t.text :internal_notes
      t.jsonb :tags, default: []
      t.integer :pin_user_ids, array: true, default: []
      t.integer :confidential_user_ids, array: true, default: []

      # Análise com IA
      t.jsonb :ai_analysis, default: {}
      t.datetime :ai_analyzed_at

      # Relacionamento com candidato importado
      t.references :candidate, foreign_key: true

      # Controle de datas
      t.datetime :profile_updated_at
      t.datetime :last_viewed_at
      t.boolean :is_deleted, default: false

      t.timestamps
    end

    add_index :sourced_profiles, :uid, unique: true
    add_index :sourced_profiles, :external_id
    add_index :sourced_profiles, [ :provider, :external_id ], unique: true
    add_index :sourced_profiles, :linkedin_slug
    add_index :sourced_profiles, :email
    add_index :sourced_profiles, :name
    add_index :sourced_profiles, :status
    add_index :sourced_profiles, :score
    add_index :sourced_profiles, :current_company
    add_index :sourced_profiles, [ :account_id, :status ]
    add_index :sourced_profiles, [ :account_id, :is_deleted ]
    add_index :sourced_profiles, [ :sourcing_id, :score ]
    add_index :sourced_profiles, :expertise, using: :gin
    add_index :sourced_profiles, :skills_data, using: :gin
    add_index :sourced_profiles, :profile_data, using: :gin
    add_index :sourced_profiles, :tags, using: :gin
  end
end
