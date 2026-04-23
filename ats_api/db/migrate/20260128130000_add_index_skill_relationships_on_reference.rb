# frozen_string_literal: true

class AddIndexSkillRelationshipsOnReference < ActiveRecord::Migration[7.1]
  def change
    add_index :skill_relationships,
              %i[reference_type reference_id],
              name: "index_skill_relationships_on_reference"
  end
end
