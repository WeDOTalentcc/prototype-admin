class AddAllowedScreeningsLimitDate < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :allowed_screenings_limit_date, :datetime, null: true unless column_exists?(:jobs, :allowed_screenings_limit_date)
  end
end
