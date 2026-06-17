# frozen_string_literal: true

load Rails.root.join("scripts", "analyze_refinement_quality_v2.rb").to_s unless defined?(RefinementQualityAnalyzerV2)

def find_testable_sourcing
  Sourcing
    .where(status: "done")
    .where("(parameters->>'search_type') = ?", "similarity")
    .joins(:candidate_feedbacks)
    .where(candidate_feedbacks: { feedback_type: "dislike" })
    .where.not(candidate_feedbacks: { reason: [ nil, "" ] })
    .order(created_at: :desc)
    .first
end

def test_sourcing_intent
  puts "\n"
  puts "=" * 80
  puts "TEST: Intent-Based Refinement (Full Report)"
  puts "=" * 80

  sourcing = find_testable_sourcing

  unless sourcing
    puts "\n⚠️  No similarity sourcing with dislike feedbacks found."
    puts "   To test this, you need to:"
    puts "   1. Create a sourcing via POST /sourcings/find_similar_candidates"
    puts "   2. Like/dislike some candidates via POST /sourcings/:id/refinements"
    puts "   3. Run this script again"
    puts "\n#{"=" * 80}\n"
    return
  end

  account = sourcing.account
  dislikes = sourcing.candidate_feedbacks.where(feedback_type: "dislike")
  likes = sourcing.candidate_feedbacks.where(feedback_type: "like")
  base_ids = sourcing.parameters&.dig("base_candidate_ids") || []
  base_names = Candidate.where(id: base_ids, account_id: account.id).pluck(:name)

  puts "\nContext:"
  puts "  Sourcing ##{sourcing.id}: #{sourcing.query}"
  puts "  Base candidates: #{base_names.join(', ')}"
  puts "  Likes: #{likes.count} | Dislikes: #{dislikes.count}"
  dislikes.each { |fb| puts "  Dislike: '#{fb.reason}'" }
  puts ""

  analyzer = RefinementQualityAnalyzerV2.new(sourcing.id, use_llm: true, test_intent_blending: true)
  analyzer.full_report

  puts "\n"
  puts "=" * 80
  puts "INTERPRETATION GUIDE"
  puts "=" * 80
  puts ""
  puts "Look for:"
  puts "  1. Intent extraction: Did LLM correctly identify desired skills from dislike reasons?"
  puts "  2. Vector shift: Intent-blended should shift MORE than vectorial-only"
  puts "  3. Skill presence: Do intent-blended results match desired skills?"
  puts "  4. 🎯 icon: Marks candidates that improved with intent-blending"
  puts ""
  puts "Success criteria:"
  puts "  • Intent extraction finds skills from dislike reasons"
  puts "  • Intent-blended shift > vectorial shift (expect ~1.5-2% vs ~0.4%)"
  puts "  • Top 5 intent results have >40% desired skill presence"
  puts ""
end

if $PROGRAM_NAME == __FILE__
  test_sourcing_intent
end
