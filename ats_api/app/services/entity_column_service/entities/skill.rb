module EntityColumnService
  module Entities
    class Skill < Base
      def columns
        [
          { key: "name", label: "Nome", type: "string" },
          { key: "skill_category_name", label: "Categoria", type: "string" },
          { key: "skill_category_icon", label: "Ícone da Categoria", type: "string" },
          { key: "skill_category_color", label: "Cor da Categoria", type: "string" },
          { key: "is_deleted", label: "Deletado", type: "boolean" },
          { key: "created_at", label: "Criado em", type: "datetime" },
          { key: "updated_at", label: "Atualizado em", type: "datetime" }
        ]
      end
    end
  end
end
