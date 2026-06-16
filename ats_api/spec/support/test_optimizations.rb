# frozen_string_literal: true

RSpec.configure do |config|
  config.before(:suite) do
    $suite_start_time = Time.now
  end

  config.after(:suite) do
    next unless $suite_start_time

    duration = Time.now - $suite_start_time
    example_count = RSpec.world.example_count

    puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "📊 Test Suite Performance:"
    puts "   Total time: #{duration.round(2)}s"
    puts "   Average: #{(duration / example_count).round(3)}s per test" if example_count > 0
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end
end
