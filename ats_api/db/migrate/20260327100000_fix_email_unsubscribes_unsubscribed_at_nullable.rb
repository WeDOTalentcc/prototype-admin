class FixEmailUnsubscribesUnsubscribedAtNullable < ActiveRecord::Migration[7.1]
  def up
    change_column_null :email_unsubscribes, :unsubscribed_at, true

    execute <<-SQL
      ALTER TABLE email_unsubscribes DROP CONSTRAINT IF EXISTS fk_rails_c141bcd8ab;
    SQL
  end

  def down
    change_column_null :email_unsubscribes, :unsubscribed_at, false
  end
end
