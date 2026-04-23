# frozen_string_literal: true

module EntityColumnService
  module Entities
    class BackgroundAgent < Base
      def self.structure
        [
          {
            value: 'name',
            text: 'Nome',
            sortable: true,
            type: 'InternalLink',
            filter: 'text',
            width: 'auto',
            min_width: '180px'
          },
          {
            value: 'target_name',
            text: 'Destino',
            sortable: false,
            type: 'text',
            filter: 'text',
            width: 'auto',
            min_width: '150px'
          },
          {
            value: 'target_type',
            text: 'Tipo',
            sortable: true,
            type: 'enum',
            filter: 'text',
            width: '80px',
            min_width: '80px'
          },
          {
            value: 'status',
            text: 'Status',
            sortable: true,
            type: 'enum',
            filter: 'text',
            width: '100px',
            min_width: '100px'
          },
          {
            value: 'mode',
            text: 'Modo',
            sortable: true,
            type: 'enum',
            filter: 'text',
            width: '90px',
            min_width: '90px'
          },
          {
            value: 'total_delivered',
            text: 'Entregues',
            sortable: true,
            type: 'text',
            width: '90px',
            min_width: '90px'
          },
          {
            value: 'total_approved',
            text: 'Aprovados',
            sortable: true,
            type: 'text',
            width: '90px',
            min_width: '90px'
          },
          {
            value: 'total_rejected',
            text: 'Rejeitados',
            sortable: true,
            type: 'text',
            width: '90px',
            min_width: '90px'
          },
          {
            value: 'approval_rate',
            text: '% Aprovação',
            sortable: false,
            type: 'text',
            width: '100px',
            min_width: '100px'
          },
          {
            value: 'daily_limit',
            text: 'Limite Diário',
            sortable: true,
            type: 'text',
            width: '100px',
            min_width: '100px'
          },
          {
            value: 'created_at',
            text: 'Criado em',
            sortable: true,
            type: 'date',
            filter: 'date',
            width: 'auto',
            min_width: '140px'
          },
          {
            value: 'updated_at',
            text: 'Atualizado em',
            sortable: true,
            type: 'date',
            filter: 'date',
            width: 'auto',
            min_width: '140px'
          }
        ]
      end
    end
  end
end
