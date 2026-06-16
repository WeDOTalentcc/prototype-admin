class AddPearchCreditSystem < ActiveRecord::Migration[7.1]
  def change
    # Adiciona créditos Pearch na tabela accounts
    add_column :accounts, :pearch_credits, :integer, default: 0, null: false
    add_column :accounts, :pearch_total_consumed, :integer, default: 0, null: false

    # Cria tabela para histórico de consumo
    create_table :pearch_search_logs do |t|
      t.references :account, null: false, foreign_key: true, index: true
      t.references :user, null: false, foreign_key: true, index: true

      # Dados da busca
      t.string :query, null: false
      t.string :thread_id
      t.string :uuid # UUID retornado pela Pearch

      # Parâmetros da busca
      t.jsonb :search_parameters, default: {}, null: false

      # Resultados
      t.integer :results_count, default: 0, null: false
      t.integer :total_estimate, default: 0
      t.boolean :total_estimate_is_lower_bound, default: false

      # Consumo de créditos
      t.integer :credits_used, null: false
      t.integer :credits_remaining_after, null: false

      # Performance
      t.float :duration_seconds
      t.string :status # Done, Failed, etc

      # Metadata
      t.jsonb :response_metadata, default: {}
      t.text :error_message

      t.timestamps
    end

    # Índices para melhor performance nas consultas
    add_index :pearch_search_logs, :created_at
    add_index :pearch_search_logs, :status
    add_index :pearch_search_logs, :credits_used
    add_index :pearch_search_logs, [ :account_id, :created_at ]
    add_index :pearch_search_logs, :search_parameters, using: :gin
  end
end
