# frozen_string_literal: true

class ChangeAllowedScreeningsLimitDateToDatetime < ActiveRecord::Migration[7.1]
  def change
    change_column :jobs, :allowed_screenings_limit_date, :datetime
  end
end
