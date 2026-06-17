class AddCandidateCompatibilityFieldsToSourcedProfiles < ActiveRecord::Migration[7.1]
  def change
    add_column :sourced_profiles, :linkedin, :string
    add_column :sourced_profiles, :github, :string
    add_column :sourced_profiles, :portfolio, :string
    add_column :sourced_profiles, :secondary_email, :string
    add_column :sourced_profiles, :mobile_phone, :string
    add_column :sourced_profiles, :secondary_phone, :string
    add_column :sourced_profiles, :street, :string
    add_column :sourced_profiles, :number, :string
    add_column :sourced_profiles, :district, :string
    add_column :sourced_profiles, :complement, :string
    add_column :sourced_profiles, :zip, :string
    add_column :sourced_profiles, :nationality, :string
    add_column :sourced_profiles, :self_introduction, :text
    add_column :sourced_profiles, :curriculum_text, :text
    add_column :sourced_profiles, :current_salary, :decimal, precision: 10, scale: 2
    add_column :sourced_profiles, :desired_salary, :decimal, precision: 10, scale: 2
    add_column :sourced_profiles, :interests, :text
    add_column :sourced_profiles, :comments, :text
    add_column :sourced_profiles, :source, :string
    add_column :sourced_profiles, :curriculum_pdf_url, :string
    add_column :sourced_profiles, :completed_register, :boolean, default: false
    add_column :sourced_profiles, :accept_terms, :boolean, default: false
  end
end
