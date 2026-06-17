#!/usr/bin/env ruby
# frozen_string_literal: true

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "🔍 Sidekiq Cron Jobs Status"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""

require_relative '../../config/environment'

Sidekiq::Cron::Job.all.each do |job|
  status_icon = job.status == "enabled" ? "✅" : "❌"

  puts "#{status_icon} #{job.name}"
  puts "   Cron: #{job.cron}"
  puts "   Class: #{job.klass}"
  puts "   Status: #{job.status}"

  if job.last_enqueue_time
    last_run = Time.parse(job.last_enqueue_time)
    ago = ((Time.now - last_run) / 60).round
    puts "   Last Run: #{last_run.strftime('%Y-%m-%d %H:%M:%S')} (#{ago}min ago)"
  else
    puts "   Last Run: Never"
  end

  if job.next_enqueue_time
    next_run = Time.parse(job.next_enqueue_time)
    in_minutes = ((next_run - Time.now) / 60).round
    puts "   Next Run: #{next_run.strftime('%Y-%m-%d %H:%M:%S')} (in #{in_minutes}min)"
  else
    puts "   Next Run: Not scheduled"
  end

  puts ""
end

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""
puts "💡 Commands:"
puts "   Reload: Sidekiq::Cron::Job.load_from_hash(YAML.load_file('config/schedule.yml'))"
puts "   Enable: Sidekiq::Cron::Job.find('job_name').enable!"
puts "   Disable: Sidekiq::Cron::Job.find('job_name').disable!"
puts "   Trigger: Sidekiq::Cron::Job.find('job_name').enque!"
puts ""
