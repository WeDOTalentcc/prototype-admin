class AddMoreFieldsInBenefits < ActiveRecord::Migration[7.1]
  def change
    add_column :benefit_relationships, :category, :string, null: true if not column_exists?(:benefit_relationships, :category)
    add_column :benefit_relationships, :provider, :string, null: true if not column_exists?(:benefit_relationships, :provider)
    add_column :benefit_relationships, :value, :decimal, precision: 10, scale: 2, null: true if not column_exists?(:benefit_relationships, :value)
    add_column :benefit_relationships, :eligibility, :jsonb, default: [], null: true if not column_exists?(:benefit_relationships, :eligibility)
    add_column :benefit_relationships, :waiting_days, :integer, null: true if not column_exists?(:benefit_relationships, :waiting_days)
    add_column :benefit_relationships, :is_active, :boolean, default: true, null: true if not column_exists?(:benefit_relationships, :is_active)
    add_column :benefit_relationships, :highlight, :boolean, default: false, null: true if not column_exists?(:benefit_relationships, :highlight)
    add_column :benefit_relationships, :required, :boolean, default: false, null: true if not column_exists?(:benefit_relationships, :required)
    add_column :benefit_relationships, :has_discount, :boolean, default: false, null: true if not column_exists?(:benefit_relationships, :has_discount)
  end

  def down
    remove_column :benefit_relationships, :category if column_exists?(:benefit_relationships, :category)
    remove_column :benefit_relationships, :provider if column_exists?(:benefit_relationships, :provider)
    remove_column :benefit_relationships, :value if column_exists?(:benefit_relationships, :value)
    remove_column :benefit_relationships, :eligibility if column_exists?(:benefit_relationships, :eligibility)
    remove_column :benefit_relationships, :waiting_days if column_exists?(:benefit_relationships, :waiting_days)
    remove_column :benefit_relationships, :is_active if column_exists?(:benefit_relationships, :is_active)
    remove_column :benefit_relationships, :highlight if column_exists?(:benefit_relationships, :highlight)
    remove_column :benefit_relationships, :required if column_exists?(:benefit_relationships, :required)
    remove_column :benefit_relationships, :has_discount if column_exists?(:benefit_relationships, :has_discount)
  end
end
