module EntityColumnService
  module Entities
    class SkillCategory < Base
      def columns
        [
          { key: "name", label: "Nome", type: "string" },
          { key: "description", label: "Descrição", type: "string" },
          { key: "icon", label: "Ícone", type: "string" },
          { key: "color", label: "Cor", type: "string" },
          { key: "skills_count", label: "Quantidade de Skills", type: "number" },
          { key: "is_deleted", label: "Deletado", type: "boolean" },
          { key: "created_at", label: "Criado em", type: "datetime" },
          { key: "updated_at", label: "Atualizado em", type: "datetime" }
        ]
      end
    end
  end
end
