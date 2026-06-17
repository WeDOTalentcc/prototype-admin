# frozen_string_literal: true

sps = SourcedProfileSourcing.find(2649)
sp = sps.sourced_profile

puts "=" * 80
puts "AI ENRICHMENT RESULTS - SourcedProfile ##{sp.id}"
puts "=" * 80
puts ""

puts "SKILLS (#{sp.skills.count} total):"
sp.skills.first(15).each do |skill|
  rel = sp.skill_relationships.find_by(skill: skill)
  level = rel&.level_skill || 0
  puts "  • #{skill.name} (level: #{level})"
end
puts ""

puts "EXPERTISE (#{(sp.expertise || []).size} items):"
(sp.expertise || []).each do |expertise|
  puts "  • [#{expertise['type']}] #{expertise['description'].truncate(80)}"
end
puts ""

puts "ENRICHMENT METADATA:"
enrichment = sp.profile_data&.dig("enrichment")
if enrichment
  puts "  ✅ Enriched at: #{enrichment['enriched_at']}"
  puts "  📊 Skills extracted: #{enrichment['skills_extracted']}"
  puts "  💡 Highlights added: #{enrichment['highlights_added']}"
  puts "  ⭐ AI Score: #{enrichment['ai_score']}"
  puts "  🎯 AI Confidence: #{enrichment['ai_confidence']}"
else
  puts "  ❌ No enrichment metadata found"
end

puts ""
puts "=" * 80
