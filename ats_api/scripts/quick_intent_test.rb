# frozen_string_literal: true

def quick_intent_test
  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "🧪 Quick Intent Extraction Test"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  sourcing = find_valid_sourcing
  unless sourcing
    puts "\n⚠️  No similarity sourcing with dislike feedbacks found."
    puts "   To test this, you need to:"
    puts "   1. Create a sourcing via POST /sourcings/find_similar_candidates"
    puts "   2. Like/dislike some candidates via POST /sourcings/:id/refinements"
    puts "   3. Run this script again"
    puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return
  end

  account = sourcing.account
  feedbacks = sourcing.candidate_feedbacks.where(feedback_type: "dislike")

  puts "\n📊 Sourcing ##{sourcing.id}: #{sourcing.query}"
  puts "   Provider: #{sourcing.provider}"
  puts "   Dislikes: #{feedbacks.count}"

  disliked = feedbacks.limit(3).map do |fb|
    candidate = Candidate.find_by(id: fb.candidate_id, account_id: account.id)
    next unless candidate

    {
      candidate_id: fb.candidate_id,
      candidate: candidate,
      reason: fb.reason.to_s
    }
  end.compact

  puts "\n🔍 Testing Intent Extraction (with gemini-2.5-flash)..."

  service = Candidates::SimilarCandidates::IntentBasedRefinementService.new
  original_centroid = Array.new(768) { rand(-0.1..0.1) }
  vectorial_refined = original_centroid.dup

  base_candidate_ids = sourcing.parameters&.dig("base_candidate_ids") || []
  base_candidates = Candidate.where(id: base_candidate_ids, account_id: account.id).to_a

  result = service.refine_with_intent(
    original_centroid: original_centroid,
    vectorial_refined: vectorial_refined,
    base_candidates: base_candidates,
    disliked_feedbacks: disliked,
    liked_candidates: []
  )

  if result != vectorial_refined
    magnitude = Math.sqrt(result.sum { |v| v**2 })
    puts "\n✅ INTENT REFINEMENT WORKED!"
    puts "   Result dimensions: #{result.size}"
    puts "   Result magnitude: #{magnitude.round(4)}"
    puts "   First 5 values: #{result.first(5).map { |v| v.round(4) }}"
    puts "\n🚀 Ready for production!"
  else
    puts "\n⚠️  Result unchanged (intent extraction may have failed)"
    puts "   Check logs for details"
  end

rescue => e
  puts "\n❌ ERROR: #{e.message}"
  puts "   #{e.class.name}"
  puts "   #{e.backtrace.first(3).join("\n   ")}"
ensure
  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
end

def find_valid_sourcing
  Sourcing
    .where(status: "done")
    .where("(parameters->>'search_type') = ?", "similarity")
    .joins(:candidate_feedbacks)
    .where(candidate_feedbacks: { feedback_type: "dislike" })
    .where.not(candidate_feedbacks: { reason: [ nil, "" ] })
    .order(created_at: :desc)
    .first
end

quick_intent_test if __FILE__ == $PROGRAM_NAME || (caller.length == 1 && caller[0].include?("rails/commands/runner"))
