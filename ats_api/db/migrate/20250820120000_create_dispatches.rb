class CreateDispatches < ActiveRecord::Migration[7.1]
  def change
    create_table :dispatches do |t|
      t.references :account, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.string :reference_type, null: true
      t.bigint :reference_id, null: true
      t.string :channel_type, null: false
      t.integer :status, null: false, default: 0
      t.string :name
      t.datetime :scheduled_for
      t.timestamps
    end unless table_exists?(:dispatches)

    add_index :dispatches, [ :reference_type, :reference_id ], name: 'index_dispatches_on_reference' unless index_exists?(:dispatches, [ :reference_type, :reference_id ], name: 'index_dispatches_on_reference')
  end
end
