# frozen_string_literal: true

puts "\n🎯 Testing Refinement with Sourcing #564"
puts "   (The one with dislike: 'nao sabe rails')"
puts "\n"

sourcing_id = 564

load 'scripts/analyze_refinement_quality.rb'

analyzer = RefinementQualityAnalyzer.new(sourcing_id)
analyzer.analyze

puts "\n"
puts "💡 WHAT TO LOOK FOR:"
puts ""
puts "1. In the DISLIKES section:"
puts "   - Shows: \"nao sabe rails\" and \"nao sabe ruby\""
puts "   - MEANING: Recruiter WANTS Rails/Ruby but rejected candidate lacks it"
puts ""
puts "2. In the VALIDATION RESULTS section:"
puts "   - Check if new candidates have Rails/Ruby in their skills"
puts "   - If they DO have Rails → ✅ GOOD (matching recruiter intent)"
puts "   - If they DON'T have Rails → ⚠️ PROBLEM (refinement didn't work)"
puts ""
puts "3. In the SEMANTIC ANALYSIS section:"
puts "   - Look for 'Recruiter WANTS candidates with: rails, ruby'"
puts "   - Check percentage of candidates with those skills"
puts "   - ❌ 0% = vectorial refinement failed to understand semantic intent"
puts ""
puts "4. Expected result for THIS test:"
puts "   - Base candidates are Java devs (not Rails)"
puts "   - Rejected candidates are also Java devs"
puts "   - ❌ System will likely find 0% Rails (wrong!)"
puts "   - This reveals the limitation: vectorial refinement is blind to text"
puts ""
