# frozen_string_literal: true

INTERVIEW_PATTERNS = /interview/i

affected = SelectiveProcess.where.not(status: SelectiveProcess.statuses[:interview])
                           .where("name ILIKE ?", "%interview%")

puts "Found #{affected.count} SelectiveProcess records to fix"

affected.find_each do |sp|
  sp.update_columns(status: SelectiveProcess.statuses[:interview])
  puts "Fixed SelectiveProcess ##{sp.id} - '#{sp.name}' (job_id: #{sp.job_id}, account_id: #{sp.account_id})"
end

puts "Done."
