# frozen_string_literal: true

puts "\n🔬 Testing Refinement V2 with Sourcing #564"
puts "   (Dislikes: 'nao sabe rails', 'nao sabe ruby')"
puts "\n"

sourcing_id = 564

load 'scripts/analyze_refinement_quality_v2.rb'

analyzer = RefinementQualityAnalyzerV2.new(sourcing_id)
analyzer.full_report

puts "\n"
puts "💡 KEY INSIGHTS TO LOOK FOR:"
puts ""
puts "1. STEP 2 - FEEDBACK INTENT:"
puts "   → Should extract: ['rails', 'ruby'] as DESIRED skills"
puts "   → 'não sabe X' means recruiter WANTS X (candidate lacked it)"
puts ""
puts "2. STEP 3 - DUAL SEARCH:"
puts "   → Compare rankings: who moved up/down with refinement?"
puts "   → Vector shift % (if < 0.1% = minimal impact)"
puts ""
puts "3. STEP 4 - CURRICULUM SCAN:"
puts "   → How many top results actually have Rails/Ruby?"
puts "   → If 0% = refinement failed to capture intent"
puts ""
puts "4. STEP 5 - VERDICT:"
puts "   → Will likely show: ineffective skill matching"
puts "   → Reason: base candidates are Java devs, rejected are also Java"
puts "   → Moving away from Java doesn't help find Rails!"
puts ""
puts "5. EXPECTED OUTCOME:"
puts "   ❌ Vector shift: ~0.4% (minimal)"
puts "   ❌ Skill match: 0% Rails/Ruby in results"
puts "   → Proves vectorial refinement is blind to textual feedback"
puts ""
