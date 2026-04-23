class AddUniqueIndexToSourcedProfileSourcings < ActiveRecord::Migration[7.1]
  def up
    duplicates_count = execute(<<~SQL).first["count"]
      SELECT COUNT(*) AS count FROM sourced_profile_sourcings
      WHERE id NOT IN (
        SELECT MIN(id)
        FROM sourced_profile_sourcings
        GROUP BY sourced_profile_id, sourcing_id
      )
    SQL

    say "Removing #{duplicates_count} duplicate sourced_profile_sourcings"

    execute <<~SQL if duplicates_count > 0
      DELETE FROM sourced_profile_sourcings
      WHERE id NOT IN (
        SELECT MIN(id)
        FROM sourced_profile_sourcings
        GROUP BY sourced_profile_id, sourcing_id
      )
    SQL

    add_index :sourced_profile_sourcings,
              [:sourced_profile_id, :sourcing_id],
              unique: true,
              name: "idx_unique_sourced_profile_sourcing"
  end

  def down
    remove_index :sourced_profile_sourcings, name: "idx_unique_sourced_profile_sourcing"
  end
end
