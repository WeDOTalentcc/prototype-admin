# frozen_string_literal: true

# =============================================================================
# INTENT-BASED REFINEMENT - FULL TEST SUITE
# =============================================================================
#
# Roda todos os testes em sequência e salva output em arquivo.
#
# Como rodar:
#   rails runner scripts/test_intent_refinement_full.rb
#
# Output salvo em: tmp/intent_refinement_test_results.txt
# =============================================================================

OUTPUT_FILE = Rails.root.join("tmp", "intent_refinement_test_results.txt")
SOURCING_ID = 564

$test_output = []
$test_results = { passed: 0, failed: 0, skipped: 0 }

def log(msg = "")
  puts msg
  $test_output << msg
end

def log_section(title)
  log ""
  log "=" * 80
  log "  #{title}"
  log "=" * 80
end

def log_step(title)
  log ""
  log "━" * 80
  log title
  log "━" * 80
end

def pass(name, detail = nil)
  $test_results[:passed] += 1
  log "  ✅ #{name}#{detail ? " — #{detail}" : ""}"
end

def fail_test(name, detail = nil)
  $test_results[:failed] += 1
  log "  ❌ #{name}#{detail ? " — #{detail}" : ""}"
end

def skip(name, detail = nil)
  $test_results[:skipped] += 1
  log "  ⏭️  #{name}#{detail ? " — #{detail}" : ""}"
end

# =============================================================================
# PHASE 1: PREREQUISITES
# =============================================================================
def phase_1_prerequisites
  log_section "PHASE 1: PREREQUISITES CHECK"

  # 1a. Sourcing exists
  log_step "1a. Sourcing ##{SOURCING_ID}"
  begin
    sourcing = Sourcing.find(SOURCING_ID)
    pass "Sourcing ##{SOURCING_ID}", (sourcing.query || sourcing.notes || "no query").truncate(50)

    base_ids = sourcing.parameters["base_candidate_ids"]
    log "     Base candidates: #{base_ids}"

    feedbacks = CandidateFeedback.where(sourcing_id: SOURCING_ID)
    likes = feedbacks.where(feedback_type: "like")
    dislikes = feedbacks.where(feedback_type: "dislike")
    log "     Likes: #{likes.count} | Dislikes: #{dislikes.count}"

    dislikes.each do |fb|
      log "     Dislike: \"#{fb.reason}\" (candidate #{fb.candidate_id}: #{fb.candidate&.name})"
    end

    pass "Feedback data present" if dislikes.count > 0
  rescue => e
    fail_test "Sourcing ##{SOURCING_ID}", e.message
    return false
  end

  # 1b. Services loaded
  log_step "1b. Service classes"
  [
    "Candidates::SimilarCandidates::EmbeddingRefinementService",
    "Candidates::SimilarCandidates::IntentBasedRefinementService",
    "Candidates::SimilarCandidates::RefinementService",
    "Embeddings::Encoder"
  ].each do |klass|
    begin
      klass.constantize
      pass klass
    rescue => e
      fail_test klass, e.message
    end
  end

  # 1c. Gemini model
  log_step "1c. Gemini API connectivity"
  working_model = nil

  %w[gemini-2.5-flash gemini-2.0-flash gemini-1.5-flash].each do |model|
    begin
      client = GeminiClient.new
      response = client.chat(
        model: model,
        messages: [ { role: "user", content: "Respond with only: OK" } ],
        temperature: 0.1,
        max_tokens: 10
      )
      content = response.dig("choices", 0, "message", "content").to_s.strip
      if content.present?
        pass "#{model}", "response: #{content.first(30)}"
        working_model = model
        break
      else
        fail_test model, "empty response"
      end
    rescue => e
      fail_test model, e.message.first(60)
    end
  end

  if working_model
    log ""
    log "  🏆 Working model: #{working_model}"
    log "     ENV GEMINI_FAST_MODEL=#{ENV['GEMINI_FAST_MODEL'] || '(not set)'}"
    if ENV['GEMINI_FAST_MODEL'] != working_model
      log "     ⚠️  Consider setting GEMINI_FAST_MODEL=#{working_model}"
    end
  else
    fail_test "No Gemini model available — intent blending will use fallback"
  end

  # 1d. Embeddings::Encoder
  log_step "1d. Embedding generation"
  begin
    encoder = Embeddings::Encoder.new
    emb = encoder.call("Senior Ruby on Rails developer")
    if emb.is_a?(Array) && emb.size > 100
      magnitude = Math.sqrt(emb.sum { |v| v**2 })
      pass "Encoder works", "#{emb.size} dims, magnitude=#{magnitude.round(4)}"
      if magnitude.round(2) == 1.0
        pass "Embeddings are normalized (unit vectors)"
      else
        log "  ⚠️  Embeddings NOT normalized (magnitude=#{magnitude.round(4)})"
        log "     IntentBasedRefinementService must normalize before blending"
      end
    else
      fail_test "Encoder", "unexpected output: #{emb.class}"
    end
  rescue => e
    fail_test "Encoder call", e.message
  end

  true
end

# =============================================================================
# PHASE 2: INTENT EXTRACTION (isolated)
# =============================================================================
def phase_2_intent_extraction
  log_section "PHASE 2: INTENT EXTRACTION"

  sourcing = Sourcing.find(SOURCING_ID)
  dislikes = CandidateFeedback.where(sourcing_id: SOURCING_ID, feedback_type: "dislike")
  likes = CandidateFeedback.where(sourcing_id: SOURCING_ID, feedback_type: "like")
  base_ids = sourcing.parameters["base_candidate_ids"]

  # 2a. Build context
  log_step "2a. Building service context"
  base_candidates = Candidate.where(id: base_ids, account_id: sourcing.account_id)
  liked_candidates = Candidate.where(id: likes.pluck(:candidate_id), account_id: sourcing.account_id)

  disliked_feedbacks = dislikes.map do |fb|
    { candidate_id: fb.candidate_id, candidate: fb.candidate, reason: fb.reason }
  end

  log "     Base candidates: #{base_candidates.map(&:name).join(', ')}"
  log "     Liked candidates: #{liked_candidates.map(&:name).join(', ')}"
  log "     Disliked feedbacks: #{disliked_feedbacks.map { |f| "#{f[:candidate]&.name}: '#{f[:reason]}'" }.join(', ')}"

  # 2b. Call IntentBasedRefinementService
  log_step "2b. LLM intent extraction"
  begin
    service = Candidates::SimilarCandidates::IntentBasedRefinementService.new

    # Access private method to test extraction in isolation
    intent_text = service.send(
      :extract_intent_description,
      base_candidates: base_candidates.to_a,
      disliked_feedbacks: disliked_feedbacks,
      liked_candidates: liked_candidates.to_a
    )

    if intent_text.present?
      pass "LLM returned intent description"
      log ""
      log "  📝 EXTRACTED INTENT:"
      log "  ┌─────────────────────────────────────────────────────────────┐"
      intent_text.lines.each { |line| log "  │ #{line.chomp.ljust(59)} │" }
      log "  └─────────────────────────────────────────────────────────────┘"

      # Check if it mentions ruby/rails
      intent_lower = intent_text.downcase
      if intent_lower.include?("ruby") || intent_lower.include?("rails")
        pass "Intent mentions Ruby/Rails (correct semantic inversion!)"
      else
        fail_test "Intent does NOT mention Ruby/Rails", "semantic inversion may have failed"
      end
    else
      fail_test "LLM returned nil/empty"
      log "     → Intent blending will fallback to vectorial-only"
    end
  rescue => e
    fail_test "Intent extraction error", "#{e.class}: #{e.message}"
    log "     #{e.backtrace.first(3).join("\n     ")}"
  end

  # 2c. Generate intent embedding
  if intent_text.present?
    log_step "2c. Intent embedding generation"
    begin
      intent_emb = service.send(:generate_intent_embedding, intent_text)
      if intent_emb.present? && intent_emb.is_a?(Array)
        magnitude = Math.sqrt(intent_emb.sum { |v| v**2 })
        pass "Intent embedding generated", "#{intent_emb.size} dims, magnitude=#{magnitude.round(4)}"
      else
        fail_test "Intent embedding nil/invalid"
      end
    rescue => e
      fail_test "Intent embedding error", e.message
    end
  end
end

# =============================================================================
# PHASE 3: FULL REFINEMENT COMPARISON
# =============================================================================
def phase_3_full_comparison
  log_section "PHASE 3: FULL REFINEMENT — 3-WAY COMPARISON"

  sourcing = Sourcing.find(SOURCING_ID)
  base_ids = sourcing.parameters["base_candidate_ids"]
  feedbacks = CandidateFeedback.where(sourcing_id: SOURCING_ID)
  likes = feedbacks.where(feedback_type: "like")
  dislikes = feedbacks.where(feedback_type: "dislike")
  liked_ids = likes.pluck(:candidate_id)
  disliked_ids = dislikes.pluck(:candidate_id)

  # Compute centroids
  log_step "3a. Computing centroids"

  vectors = Embedding.where(reference_type: "Candidate", reference_id: base_ids).pluck(:embedding)
  return fail_test("No embeddings for base candidates") if vectors.empty?

  dims = vectors.first.size
  original_centroid = Array.new(dims, 0.0)
  vectors.each { |vec| vec.each_with_index { |v, i| original_centroid[i] += v } }
  original_centroid.map! { |v| v / vectors.size }
  log "     Original centroid: #{dims} dims"

  # Vectorial refinement
  vec_service = Candidates::SimilarCandidates::EmbeddingRefinementService.new(
    original_centroid: original_centroid
  )
  vectorial_centroid = vec_service.refine(liked_ids: liked_ids, disliked_ids: disliked_ids)

  vec_sim = cosine_similarity(original_centroid, vectorial_centroid)
  vec_shift = ((1 - vec_sim) * 100).round(4)
  log "     Vectorial shift: #{vec_shift}% (similarity: #{(vec_sim * 100).round(2)}%)"

  # Intent refinement
  base_candidates = Candidate.where(id: base_ids, account_id: sourcing.account_id)
  liked_candidates = Candidate.where(id: liked_ids, account_id: sourcing.account_id)
  disliked_feedbacks = dislikes.map { |fb| { candidate_id: fb.candidate_id, candidate: fb.candidate, reason: fb.reason } }

  intent_service = Candidates::SimilarCandidates::IntentBasedRefinementService.new
  intent_centroid = intent_service.refine_with_intent(
    original_centroid: original_centroid,
    vectorial_refined: vectorial_centroid,
    base_candidates: base_candidates,
    disliked_feedbacks: disliked_feedbacks,
    liked_candidates: liked_candidates
  )

  intent_sim = cosine_similarity(original_centroid, intent_centroid)
  intent_shift = ((1 - intent_sim) * 100).round(4)
  log "     Intent shift:     #{intent_shift}% (similarity: #{(intent_sim * 100).round(2)}%)"

  vec_vs_intent = cosine_similarity(vectorial_centroid, intent_centroid)
  diff = ((1 - vec_vs_intent) * 100).round(4)
  log "     Vec↔Intent diff:  #{diff}%"

  if diff > 0.01
    pass "Intent centroid DIFFERS from vectorial", "#{diff}% divergence"
  else
    fail_test "Intent centroid IDENTICAL to vectorial", "LLM likely failed (fallback)"
  end

  # Search with all 3 centroids
  log_step "3b. Running 3-way search"

  existing_ids = SourcedProfileSourcing
    .joins(:sourced_profile)
    .where(sourcing_id: SOURCING_ID, is_deleted: false)
    .pluck("sourced_profiles.candidate_id")
  exclude_ids = (base_ids + liked_ids + disliked_ids + existing_ids).uniq
  threshold = 0.60
  limit = 15

  original_results = vector_search(original_centroid, exclude_ids, threshold, limit)
  vectorial_results = vector_search(vectorial_centroid, exclude_ids, threshold, limit)
  intent_results = vector_search(intent_centroid, exclude_ids, threshold, limit)

  log "     Original: #{original_results.size} results"
  log "     Vectorial: #{vectorial_results.size} results"
  log "     Intent: #{intent_results.size} results"

  # Comparison table
  log_step "3c. Results comparison"

  all_ids = (original_results + vectorial_results + intent_results).map { |r| r[:id] }.uniq
  candidates = Candidate.where(id: all_ids, account_id: sourcing.account_id).index_by(&:id)

  orig_map = original_results.each_with_object({}) { |r, h| h[r[:id]] = r[:score] }
  vec_map = vectorial_results.each_with_object({}) { |r, h| h[r[:id]] = r[:score] }
  int_map = intent_results.each_with_object({}) { |r, h| h[r[:id]] = r[:score] }

  # Build rows sorted by intent score (or vec, or orig)
  rows = all_ids.map do |id|
    cand = candidates[id]
    {
      id: id,
      name: cand&.name || "?",
      role: cand&.role_name || "",
      orig: orig_map[id],
      vec: vec_map[id],
      intent: int_map[id],
      candidate: cand
    }
  end.sort_by { |r| -(r[:intent] || r[:vec] || r[:orig] || 0) }

  # Print table
  log ""
  log "  %-6s %-28s %-8s %-8s %-8s %-6s %-6s" % [ "ID", "Name", "Orig%", "Vec%", "Intent%", "ruby", "rails" ]
  log "  " + "─" * 90

  desired_skills = %w[ruby rails]
  skill_counts = { orig: 0, vec: 0, intent: 0 }

  rows.take(15).each do |row|
    cand = row[:candidate]
    text = (cand&.curriculum_text || "").downcase + " " + (cand&.role_name || "").downcase

    has_ruby = text.include?("ruby") ? "✓" : "✗"
    has_rails = text.include?("rails") || text.include?("ror") ? "✓" : "✗"
    has_any = has_ruby == "✓" || has_rails == "✓"

    skill_counts[:intent] += 1 if has_any && row[:intent]
    skill_counts[:vec] += 1 if has_any && row[:vec]
    skill_counts[:orig] += 1 if has_any && row[:orig]

    log "  %-6d %-28s %-8s %-8s %-8s %-6s %-6s" % [
      row[:id],
      row[:name].to_s.truncate(26),
      row[:orig] ? "#{"%.1f" % (row[:orig] * 100)}%" : "-",
      row[:vec] ? "#{"%.1f" % (row[:vec] * 100)}%" : "-",
      row[:intent] ? "#{"%.1f" % (row[:intent] * 100)}%" : "-",
      has_ruby,
      has_rails
    ]
  end

  log "  " + "─" * 90

  # Skill summary
  log_step "3d. Skill match summary"
  orig_total = original_results.size.clamp(1, 15)
  vec_total = vectorial_results.size.clamp(1, 15)
  int_total = intent_results.size.clamp(1, 15)

  log "     Original:  #{skill_counts[:orig]}/#{[ original_results.size, 15 ].min} have Ruby/Rails"
  log "     Vectorial: #{skill_counts[:vec]}/#{[ vectorial_results.size, 15 ].min} have Ruby/Rails"
  log "     Intent:    #{skill_counts[:intent]}/#{[ intent_results.size, 15 ].min} have Ruby/Rails"

  if skill_counts[:intent] > skill_counts[:vec]
    pass "Intent blending IMPROVED skill matching!", "#{skill_counts[:intent]} vs #{skill_counts[:vec]}"
  elsif skill_counts[:intent] == skill_counts[:vec] && skill_counts[:intent] > 0
    log "  ⚠️  Same skill count — check if different candidates"
  elsif skill_counts[:intent] == 0
    fail_test "No Ruby/Rails candidates in intent results"
    log "     → May need higher GAMMA or different approach"
  end

  # Only-in-intent (new candidates surfaced by intent)
  intent_only_ids = intent_results.map { |r| r[:id] } - vectorial_results.map { |r| r[:id] }
  if intent_only_ids.any?
    log ""
    log "  🆕 Candidates ONLY in intent results (not in vectorial):"
    intent_only_ids.take(5).each do |id|
      cand = candidates[id]
      text = (cand&.curriculum_text || "").downcase
      has_skill = text.include?("ruby") || text.include?("rails")
      score = int_map[id]
      log "     • #{cand&.name} (#{"%.1f" % (score * 100)}%) #{has_skill ? '← HAS RUBY/RAILS ✓' : ''}"
    end
  end
end

# =============================================================================
# PHASE 4: VERDICT
# =============================================================================
def phase_4_verdict
  log_section "PHASE 4: VERDICT"
  log ""
  log "  Passed: #{$test_results[:passed]}"
  log "  Failed: #{$test_results[:failed]}"
  log "  Skipped: #{$test_results[:skipped]}"
  log ""

  if $test_results[:failed] == 0
    log "  🎉 ALL TESTS PASSED — Intent refinement is working!"
  elsif $test_results[:failed] <= 2
    log "  ⚠️  PARTIAL SUCCESS — Some issues to address"
  else
    log "  ❌ SIGNIFICANT ISSUES — Review failures above"
  end

  log ""
  log "  Generated: #{Time.current.strftime('%Y-%m-%d %H:%M:%S')}"
  log "  Rails env: #{Rails.env}"
  log "  GEMINI_FAST_MODEL: #{ENV['GEMINI_FAST_MODEL'] || '(not set)'}"
end

# =============================================================================
# HELPERS
# =============================================================================
def cosine_similarity(v1, v2)
  dot = v1.zip(v2).sum { |a, b| a * b }
  m1 = Math.sqrt(v1.sum { |v| v**2 })
  m2 = Math.sqrt(v2.sum { |v| v**2 })
  return 0.0 if m1.zero? || m2.zero?
  dot / (m1 * m2)
end

def vector_search(centroid, exclude_ids, threshold, limit)
  # Raw SQL with explicit vector cast for pgvector
  # Need to set search_path to include extensions schema where vector type is defined
  embedding_str = "[#{centroid.join(',')}]"

  sql = <<~SQL
    SET LOCAL search_path = public, extensions;
    SELECT#{' '}
      reference_id,
      1 - (embedding <=> '#{embedding_str}'::vector) AS similarity
    FROM embeddings
    WHERE reference_type = 'Candidate'
      AND reference_id NOT IN (#{exclude_ids.any? ? exclude_ids.join(',') : '0'})
      AND (1 - (embedding <=> '#{embedding_str}'::vector)) >= #{threshold}
    ORDER BY embedding <=> '#{embedding_str}'::vector
    LIMIT #{limit}
  SQL

  results = ActiveRecord::Base.connection.execute(sql)
  results.map { |row| { id: row['reference_id'].to_i, score: row['similarity'].to_f } }
rescue => e
  log "  ❌ Search error: #{e.message}"
  []
end

# =============================================================================
# RUN
# =============================================================================
log_section "INTENT-BASED REFINEMENT — FULL TEST SUITE"
log "  Sourcing: ##{SOURCING_ID}"
log "  Time: #{Time.current.strftime('%Y-%m-%d %H:%M:%S')}"
log "  Environment: #{Rails.env}"

phase_1_prerequisites
phase_2_intent_extraction
phase_3_full_comparison
phase_4_verdict

# Save to file
File.write(OUTPUT_FILE, $test_output.join("\n"))
log ""
log "📄 Results saved to: #{OUTPUT_FILE}"
log "   Copy with: cat #{OUTPUT_FILE} | pbcopy"
log "   Or: cat #{OUTPUT_FILE}"
