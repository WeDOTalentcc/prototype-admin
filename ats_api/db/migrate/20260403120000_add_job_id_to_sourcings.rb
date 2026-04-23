# frozen_string_literal: true

class AddJobIdToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_reference :sourcings, :job, null: true, foreign_key: true, index: true
  end
end
