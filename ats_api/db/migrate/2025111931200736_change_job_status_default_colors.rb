class ChangeJobStatusDefaultColors < ActiveRecord::Migration[7.1]
  def change
    JobStatus::DEFAULT_STATUSES.each do |status_attributes|
      status = JobStatus.find_by(name: status_attributes[:name])

      if status.present?
        status.update(color: status_attributes[:color])
      end
    end
  end
end
