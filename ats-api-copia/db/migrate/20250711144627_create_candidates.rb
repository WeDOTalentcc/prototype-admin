class CreateCandidates < ActiveRecord::Migration[7.1]
  def change
    create_table :candidates do |t|
      # Identificação e contato
      t.string :uid
      t.string :name
      t.string :surname
      t.string :email, default: ""
      t.string :secondary_email
      t.string :mobile_phone
      t.string :phone
      t.string :secondary_phone
      t.string :linkedin
      t.string :github
      t.string :portfolio
      t.string :current_company
      t.string :role_name
      t.string :position_level
      t.text :self_introduction
      t.text :curriculum_text

      # Dados pessoais
      t.date :date_birth
      t.integer :gender
      t.string :nationality
      t.integer :marital_status
      t.string :cpf

      # Endereço
      t.string :street
      t.integer :number
      t.string :district
      t.string :zip
      t.string :city
      t.string :state
      t.string :country
      t.string :complement

      # Expectativas salariais
      t.float :clt_expectation, default: 0.0
      t.float :pj_expectation, default: 0.0
      t.float :freelance_expectation, default: 0.0
      t.float :current_salary, default: 0.0
      t.float :desired_salary
      t.string :currency, default: "BRL"

      # Mobilidade e disponibilidade
      t.boolean :remote_work
      t.boolean :mobility, default: true

      # Outras características
      t.string :interests
      t.text :comments
      t.string :source

      # Dados de currículo/arquivos
      t.string :avatar_url
      t.string :curriculum_pdf_url

      # Flags gerais
      t.boolean :completed_register, default: false
      t.boolean :accept_terms, default: false

      t.timestamps
    end

    add_index :candidates, :email
    add_index :candidates, :uid
    add_index :candidates, :linkedin
  end
end
