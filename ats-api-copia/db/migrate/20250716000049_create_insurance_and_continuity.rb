# frozen_string_literal: true

class CreateInsuranceAndContinuity < ActiveRecord::Migration[7.1]
  def change
    create_table :insurance_policies, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :policy_type, limit: 50
      t.string :provider, limit: 200
      t.string :policy_number, limit: 100
      t.date :start_date
      t.date :end_date
      t.decimal :premium, precision: 12, scale: 2
      t.string :status, limit: 20, default: "active"
      t.jsonb :coverage_details, default: {}
      t.timestamps
    end
    add_index :insurance_policies, :company_id

    create_table :insurance_coverages, id: :uuid do |t|
      t.references :insurance_policy, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :coverage_type, limit: 50
      t.decimal :limit_amount, precision: 12, scale: 2
      t.decimal :deductible, precision: 12, scale: 2
      t.text :description
      t.timestamps
    end

    create_table :insurance_documents, id: :uuid do |t|
      t.references :insurance_policy, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :document_type, limit: 50
      t.string :file_url, limit: 500
      t.string :file_name, limit: 200
      t.timestamps
    end

    create_table :insurance_claims, id: :uuid do |t|
      t.references :insurance_policy, type: :uuid, null: false, foreign_key: { on_delete: :cascade }
      t.string :claim_number, limit: 100
      t.date :incident_date
      t.text :description
      t.string :status, limit: 20, default: "submitted"
      t.decimal :claimed_amount, precision: 12, scale: 2
      t.decimal :approved_amount, precision: 12, scale: 2
      t.timestamps
    end

    create_table :disaster_recovery_plans, id: :uuid do |t|
      t.string :company_id, null: false
      t.string :name, limit: 200
      t.text :description
      t.string :plan_type, limit: 50
      t.jsonb :procedures, default: []
      t.string :status, limit: 20, default: "draft"
      t.datetime :last_tested_at
      t.string :approved_by
      t.timestamps
    end
    add_index :disaster_recovery_plans, :company_id

    create_table :continuity_tests, id: :uuid do |t|
      t.references :disaster_recovery_plan, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :test_type, limit: 50
      t.date :test_date
      t.string :result, limit: 20
      t.jsonb :findings, default: []
      t.text :notes
      t.string :conducted_by
      t.timestamps
    end
  end
end
