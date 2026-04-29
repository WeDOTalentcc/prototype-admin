class AddSearchArchetypeToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_reference :sourcings, :search_archetype, null: true, foreign_key: true
  end
end
