# frozen_string_literal: true

PHASE_WIDTH = 90

def refinement_visual_demo
  puts "\n"
  puts "█" * PHASE_WIDTH
  puts "█#{"REFINEMENT SYSTEM — VISUAL EVIDENCE".center(PHASE_WIDTH - 2)}█"
  puts "█" * PHASE_WIDTH

  sourcing = find_demo_sourcing
  unless sourcing
    print_no_sourcing_warning
    return
  end

  account = sourcing.account

  Apartment::Tenant.switch(account.tenant) do
    run_demo_pipeline(sourcing, account)
  end
end

def run_demo_pipeline(sourcing, account)
  context = load_demo_context(sourcing, account)

  print_phase_header("PHASE 0", "INPUT — Sourcing Context & Feedback")
  print_sourcing_context(sourcing, context)
  print_feedback_summary(context)

  original_centroid = compute_demo_centroid(context[:base_candidate_ids])
  unless original_centroid
    puts "\n  ❌ No embeddings found for base candidates. Cannot proceed."
    return
  end

  print_phase_header("PHASE 1", "VECTORIAL REFINEMENT (EmbeddingRefinementService)")
  vectorial_centroid = run_vectorial_refinement(original_centroid, context)
  print_vectorial_phase(original_centroid, vectorial_centroid, context)

  print_phase_header("PHASE 2", "LLM INTENT EXTRACTION (IntentBasedRefinementService → Gemini 2.5 Flash)")
  intent_result = run_intent_refinement(original_centroid, vectorial_centroid, context)
  blended_embedding = intent_result[:centroid] || vectorial_centroid
  print_intent_phase(intent_result, original_centroid, vectorial_centroid)

  exclude_ids = build_demo_exclude_ids(context)
  threshold = sourcing.search_metadata&.dig("threshold")&.to_f || 0.60

  print_phase_header("PHASE 3", "HYBRID SEARCH — pgvector + Elasticsearch + RRF Fusion")
  print_hybrid_explainer(intent_result)

  original_candidates = search_candidates(original_centroid, exclude_ids, threshold, 10, account)
  vector_candidates = search_candidates(blended_embedding, exclude_ids, threshold, 60, account)
  text_candidates = run_text_search(intent_result, exclude_ids, account)

  print_dual_source_results(vector_candidates, text_candidates, intent_result)

  hybrid_candidates = run_hybrid_fusion(vector_candidates, text_candidates, 10)
  print_rrf_fusion(hybrid_candidates)

  print_phase_header("PHASE 4", "BEFORE vs AFTER — Impact Comparison")
  print_results_comparison(original_candidates, hybrid_candidates.presence || vector_candidates.first(10))

  all_desired = build_desired_skills(intent_result)
  print_skill_scan(hybrid_candidates.presence || vector_candidates.first(10), all_desired) if all_desired.any?

  print_phase_header("VERDICT", "System Assessment")
  print_final_verdict(original_candidates, vector_candidates, hybrid_candidates, intent_result)

  puts "\n#{"█" * PHASE_WIDTH}\n"
end

def find_demo_sourcing
  sourcing_id = ENV["SOURCING_ID"]
  return Sourcing.find(sourcing_id) if sourcing_id.present?

  Sourcing
    .where(status: "done")
    .where("(parameters->>'search_type') = ?", "similarity")
    .joins(:candidate_feedbacks)
    .where(candidate_feedbacks: { feedback_type: "dislike" })
    .where.not(candidate_feedbacks: { reason: [ nil, "" ] })
    .order(created_at: :desc)
    .first
end

def print_no_sourcing_warning
  puts "\n  ⚠️  No similarity sourcing with dislike feedbacks found."
  puts ""
  puts "  To generate visual evidence, you need to:"
  puts "  ┌──────────────────────────────────────────────────────────────────┐"
  puts "  │ 1. POST /sourcings/find_similar_candidates                     │"
  puts "  │    { candidate_ids: [123], sources: ['local'] }                │"
  puts "  │                                                                │"
  puts "  │ 2. POST /sourcings/:id/refinements                            │"
  puts "  │    { liked_candidate_ids: [456],                               │"
  puts "  │      disliked_feedbacks: [                                     │"
  puts "  │        { candidate_id: 789, reason: 'not ruby' }              │"
  puts "  │      ]                                                         │"
  puts "  │    }                                                           │"
  puts "  │                                                                │"
  puts "  │ 3. Run this script again                                       │"
  puts "  └──────────────────────────────────────────────────────────────────┘"
  puts "\n#{"█" * PHASE_WIDTH}\n"
end

def print_phase_header(phase, title)
  puts "\n"
  puts "  ┏#{"━" * (PHASE_WIDTH - 4)}┓"
  puts "  ┃ #{phase.ljust(10)} #{title.truncate(PHASE_WIDTH - 18).ljust(PHASE_WIDTH - 17)}┃"
  puts "  ┗#{"━" * (PHASE_WIDTH - 4)}┛"
end

def load_demo_context(sourcing, account)
  base_ids = sourcing.parameters&.dig("base_candidate_ids") || []
  base_candidates = Candidate.where(id: base_ids, account_id: account.id).to_a
  likes = sourcing.candidate_feedbacks.where(feedback_type: "like")
  dislikes = sourcing.candidate_feedbacks.where(feedback_type: "dislike")

  liked_candidates = Candidate.where(id: likes.pluck(:candidate_id), account_id: account.id).to_a

  disliked_feedbacks = dislikes.filter_map do |fb|
    candidate = Candidate.find_by(id: fb.candidate_id, account_id: account.id)
    next unless candidate

    { candidate_id: fb.candidate_id, candidate: candidate, reason: fb.reason.to_s }
  end

  {
    base_candidate_ids: base_ids,
    base_candidates: base_candidates,
    liked_ids: likes.pluck(:candidate_id),
    liked_candidates: liked_candidates,
    disliked_feedbacks: disliked_feedbacks,
    account: account
  }
end

def print_sourcing_context(sourcing, context)
  puts "\n  ┌─ SOURCING ##{sourcing.id} #{"─" * [ 1, 65 - sourcing.id.to_s.length ].max}┐"
  puts "  │  Query: #{sourcing.query.to_s.truncate(60).ljust(63)}│"
  puts "  │  Provider: #{sourcing.provider.to_s.ljust(60)}│"
  puts "  │  Created: #{sourcing.created_at.strftime('%Y-%m-%d %H:%M').ljust(61)}│"
  puts "  └#{"─" * (PHASE_WIDTH - 4)}┘"

  puts "\n  👥 BASE CANDIDATES (initial search seeds):"
  context[:base_candidates].each do |c|
    skills = extract_demo_skills(c).take(6).join(", ")
    puts "     ├─ #{c.name}"
    puts "     │  Role: #{c.role_name || 'N/A'}"
    puts "     │  Skills: #{skills.presence || '(none detected)'}"
  end
end

def print_feedback_summary(context)
  puts "\n  ✅ LIKED (#{context[:liked_candidates].size}):"
  context[:liked_candidates].each do |c|
    puts "     ├─ #{c.name} — #{c.role_name || 'N/A'}"
  end
  puts "     └─ (none)" if context[:liked_candidates].empty?

  puts "\n  ❌ DISLIKED (#{context[:disliked_feedbacks].size}):"
  context[:disliked_feedbacks].each do |df|
    puts "     ├─ #{df[:candidate].name}"
    puts "     │  Reason: \"#{df[:reason]}\""
  end
end

def compute_demo_centroid(candidate_ids)
  vectors = Embedding
    .where(reference_type: "Candidate", reference_id: candidate_ids)
    .pluck(:embedding)

  return nil if vectors.empty?
  return vectors.first if vectors.size == 1

  dims = vectors.first.size
  centroid = Array.new(dims, 0.0)
  vectors.each { |vec| vec.each_with_index { |v, i| centroid[i] += v } }
  centroid.map { |v| v / vectors.size }
end

def run_vectorial_refinement(original_centroid, context)
  Candidates::SimilarCandidates::EmbeddingRefinementService.new(
    original_centroid: original_centroid
  ).refine(
    liked_ids: context[:liked_ids],
    disliked_ids: context[:disliked_feedbacks].map { |d| d[:candidate_id] }
  )
end

def print_vectorial_phase(original, vectorial, context)
  shift = centroid_shift_pct(original, vectorial)

  puts "\n  How it works:"
  puts "    centroid_new = centroid + α·(liked_centroid − centroid) − β·(disliked_centroid − centroid)"
  puts "    α = 0.3 (attraction to likes)    β = 0.2 (repulsion from dislikes)"
  puts ""
  puts "  Input:"
  puts "    ├─ Original centroid: 768-dim vector (average of #{context[:base_candidate_ids].size} base embeddings)"
  puts "    ├─ #{context[:liked_ids].size} liked candidate(s) → pull centroid TOWARDS"
  puts "    └─ #{context[:disliked_feedbacks].size} disliked candidate(s) → push centroid AWAY"
  puts ""
  puts "  Result:"
  bar = progress_bar(shift, 5.0, 30)
  puts "    📐 Centroid shift: #{format("%.4f", shift)}%  #{bar}"
end

def run_intent_refinement(original_centroid, vectorial_centroid, context)
  empty_result = { centroid: nil, description: nil, desired_skills: [], worked: false,
                   searchable: [], not_searchable: [], es_query: nil, must_have: [], nice_to_have: [] }
  return empty_result if context[:disliked_feedbacks].empty?

  intent_result = Candidates::SimilarCandidates::IntentBasedRefinementService.new.refine_with_intent(
    original_centroid: original_centroid,
    vectorial_refined: vectorial_centroid,
    base_candidates: context[:base_candidates],
    disliked_feedbacks: context[:disliked_feedbacks],
    liked_candidates: context[:liked_candidates]
  )

  {
    centroid: intent_result.skipped ? nil : intent_result.embedding,
    description: intent_result.description,
    desired_skills: extract_desired_skills_from_feedback(context[:disliked_feedbacks]),
    worked: !intent_result.skipped,
    searchable: Array(intent_result.searchable_attributes),
    not_searchable: Array(intent_result.not_searchable_feedback),
    es_query: intent_result.elasticsearch_query,
    must_have: Array(intent_result.must_have_skills),
    nice_to_have: Array(intent_result.nice_to_have_skills)
  }
end

def print_intent_phase(intent_result, original, vectorial)
  puts "\n  How it works:"
  puts "    1. Send base candidates + feedback to Gemini 2.5 Flash"
  puts "    2. LLM classifies each feedback → SEARCHABLE or NOT_SEARCHABLE"
  puts "    3. LLM generates: ideal_candidate_description + elasticsearch_query"
  puts "    4. Embed description → blend: final = normalize(0.75·vectorial + 0.25·intent)"
  puts ""

  if intent_result[:description]
    puts "  ┌─ LLM Response ──────────────────────────────────────────────────────────────┐"
    puts "  │                                                                              │"
    puts "  │  🧠 IDEAL CANDIDATE DESCRIPTION:                                             │"
    word_wrap(intent_result[:description], 70).each do |line|
      puts "  │     #{line.ljust(77)}│"
    end

    if intent_result[:searchable].any?
      puts "  │                                                                              │"
      attrs = intent_result[:searchable].join(", ")
      puts "  │  ✅ SEARCHABLE: #{attrs.truncate(63).ljust(67)}│"
    end

    if intent_result[:es_query].present?
      puts "  │                                                                              │"
      puts "  │  🔍 ES QUERY: \"#{intent_result[:es_query].truncate(63)}\"#{" " * [ 1, 65 - intent_result[:es_query].truncate(63).length ].max}│"
    end

    if intent_result[:must_have].present? && intent_result[:must_have].any?
      mh = intent_result[:must_have].join(", ")
      puts "  │  🎯 MUST HAVE: [#{mh.truncate(62)}]#{" " * [ 1, 64 - mh.truncate(62).length ].max}│"
    end

    if intent_result[:nice_to_have].present? && intent_result[:nice_to_have].any?
      nh = intent_result[:nice_to_have].join(", ")
      puts "  │  💡 NICE TO HAVE: [#{nh.truncate(59)}]#{" " * [ 1, 61 - nh.truncate(59).length ].max}│"
    end

    if intent_result[:not_searchable].any?
      puts "  │                                                                              │"
      puts "  │  ⚠️  NOT_SEARCHABLE (excluded from embedding & ES):                           │"
      intent_result[:not_searchable].each do |ns|
        fb = ns.is_a?(Hash) ? (ns["feedback"] || ns[:feedback]) : ns.to_s
        tp = ns.is_a?(Hash) ? (ns["type"] || ns[:type]) : "unknown"
        puts "  │     ✗ #{fb.to_s.truncate(50).ljust(50)} [#{tp.to_s.ljust(12)}]          │"
      end
    end

    puts "  │                                                                              │"
    puts "  └──────────────────────────────────────────────────────────────────────────────┘"
  end

  puts ""
  puts "  Embedding blending:"

  return unless intent_result[:worked]

  intent_centroid = intent_result[:centroid]
  vec_shift = centroid_shift_pct(original, vectorial)
  int_shift = intent_centroid ? centroid_shift_pct(original, intent_centroid) : 0
  amplification = int_shift > 0 && vec_shift > 0 ? (int_shift / vec_shift).round(1) : 0

  puts "    blended = normalize( 0.75 · vectorial_centroid + 0.25 · intent_embedding )"
  puts ""
  puts "    📐 Vectorial shift:  #{format("%.4f", vec_shift)}%  #{progress_bar(vec_shift, 5.0, 30)}"
  puts "    🧠 Blended shift:    #{format("%.4f", int_shift)}%  #{progress_bar(int_shift, 5.0, 30)}"
  puts "    📊 Amplification:    #{format("%.1fx", amplification)}"
  puts ""
  puts "    The blended embedding is what goes into pgvector search below ↓"
end

def print_hybrid_explainer(intent_result)
  puts "\n  Pipeline:"
  puts "    ┌─────────────────────────┐     ┌──────────────────────────────┐"
  puts "    │   BLENDED EMBEDDING     │     │   LLM-GENERATED ES QUERY    │"
  puts "    │  (from Phase 1 + 2)     │     │  \"#{(intent_result[:es_query] || 'N/A').truncate(26)}\"  │"
  puts "    └──────────┬──────────────┘     └──────────────┬───────────────┘"
  puts "               │                                   │"
  puts "               ▼                                   ▼"
  puts "    ┌──────────────────────┐         ┌──────────────────────────┐"
  puts "    │   🟦 PGVECTOR        │         │   🟨 ELASTICSEARCH       │"
  puts "    │   cosine similarity  │         │   text match (Searchkick)│"
  puts "    │   pool: 60 results   │         │   limit: 15 results      │"
  puts "    └──────────┬───────────┘         └──────────────┬───────────┘"
  puts "               │                                    │"
  puts "               └────────────┬───────────────────────┘"
  puts "                            ▼"
  puts "               ┌─────────────────────────────┐"
  puts "               │   🔗 RRF FUSION              │"
  puts "               │   score = 0.6/(60+r_vec)     │"
  puts "               │        + 0.4/(60+r_txt)      │"
  puts "               │   interleave: 30% text min   │"
  puts "               └──────────┬──────────────────┘"
  puts "                          ▼"
  puts "               ┌─────────────────────────────┐"
  puts "               │   TOP 10 FINAL RESULTS      │"
  puts "               └─────────────────────────────┘"

  return if intent_result[:es_query].present?

  puts ""
  puts "    ⚠️  No ES query from LLM → text search SKIPPED → vector-only results"
end

def run_text_search(intent_result, exclude_ids, account)
  return [] unless intent_result[:es_query].present?

  Candidates::SimilarCandidates::TextSearchService.new(account_id: account.id).search(
    query: intent_result[:es_query],
    exclude_ids: exclude_ids,
    must_have_skills: intent_result[:must_have],
    limit: 15
  ).map do |r|
    cand = Candidate.find_by(id: r[:candidate_id], account_id: account.id)
    next unless cand

    r.merge(
      similarity: ((r[:similarity] || 0) * 100).round(1),
      name: cand.name,
      role: cand.role_name,
      skills: extract_demo_skills(cand)
    )
  end.compact
rescue => e
  Rails.logger.error "[VisualEvidence] Text search failed: #{e.message}"
  []
end

def run_hybrid_fusion(vector_results, text_results, limit)
  return vector_results.first(limit) if text_results.empty?
  return text_results.first(limit) if vector_results.empty?

  vec_input = vector_results.map { |r| { candidate_id: r[:candidate_id], similarity: (r[:similarity] || 0) / 100.0 } }
  txt_input = text_results.map { |r| { candidate_id: r[:candidate_id], similarity: (r[:similarity] || 0) / 100.0 } }

  fused = Candidates::SimilarCandidates::RankFusionService.new.fuse(
    vector_results: vec_input,
    text_results: txt_input,
    limit: limit
  )

  all_data = (vector_results + text_results).index_by { |r| r[:candidate_id] }

  fused.map do |result|
    existing = all_data[result[:candidate_id]] || {}
    {
      candidate_id: result[:candidate_id],
      similarity: ((result[:similarity] || 0) * 100).round(1),
      rrf_score: result[:rrf_score],
      name: existing[:name],
      role: existing[:role],
      skills: existing[:skills] || [],
      source: result[:source]
    }
  end
end

def print_dual_source_results(vector_results, text_results, intent_result)
  col_w = 42

  puts "\n"
  puts "  ┌#{"─" * col_w}┐  ┌#{"─" * col_w}┐"
  puts "  │ #{"🟦 PGVECTOR RESULTS".ljust(col_w - 1)}│  │ #{"🟨 ELASTICSEARCH RESULTS".ljust(col_w - 1)}│"
  puts "  │ #{"Source: blended embedding (cosine sim)".ljust(col_w - 1)}│  │ #{"Source: LLM ES query (text match)".ljust(col_w - 1)}│"
  puts "  ├#{"─" * col_w}┤  ├#{"─" * col_w}┤"

  vec_count = "Pool: #{vector_results.size} candidates"
  if intent_result[:es_query].blank?
    txt_count = "⚠️  SKIPPED (no ES query)"
  else
    txt_count = "Found: #{text_results.size} candidates"
  end
  puts "  │ #{vec_count.ljust(col_w - 1)}│  │ #{txt_count.ljust(col_w - 1)}│"
  puts "  ├#{"─" * col_w}┤  ├#{"─" * col_w}┤"

  max_rows = [ [ vector_results.size, text_results.size ].max, 10 ].min

  max_rows.times do |i|
    vec = vector_results[i]
    txt = text_results[i]

    vec_line = vec ? format(" %2d. %-21s %5.1f%%", i + 1, vec[:name].to_s.truncate(19), vec[:similarity]) : ""
    txt_line = txt ? format(" %2d. %-21s %5.1f%%", i + 1, txt[:name].to_s.truncate(19), txt[:similarity]) : ""

    puts "  │#{vec_line.ljust(col_w)}│  │#{txt_line.ljust(col_w)}│"
  end

  [ vector_results.size, text_results.size ].each_with_index do |size, idx|
    next unless size > max_rows

    remaining = size - max_rows
    msg = format(" ... +%d more", remaining)
    if idx == 0
      puts "  │#{msg.ljust(col_w)}│  │#{"".ljust(col_w)}│"
    else
      puts "  │#{"".ljust(col_w)}│  │#{msg.ljust(col_w)}│"
    end
  end

  puts "  └#{"─" * col_w}┘  └#{"─" * col_w}┘"

  return unless text_results.any? && intent_result[:must_have].present?

  must_have = intent_result[:must_have]
  with_skills = text_results.count do |t|
    full_text = build_full_text(t)
    must_have.all? { |s| full_text.include?(s.downcase) }
  end
  puts "\n  📊 ES quality: #{with_skills}/#{text_results.size} have ALL must-have skills (#{must_have.join(", ")})"

  overlap = vector_results.map { |v| v[:candidate_id] } & text_results.map { |t| t[:candidate_id] }
  puts "  🔗 Overlap: #{overlap.size} candidates appear in BOTH sources"
end

def print_rrf_fusion(hybrid_candidates)
  return if hybrid_candidates.empty?

  both = hybrid_candidates.count { |c| c[:source] == :both }
  vec_only = hybrid_candidates.count { |c| c[:source] == :vector }
  txt_only = hybrid_candidates.count { |c| c[:source] == :text }
  source_icons = { both: "🔗", vector: "🟦", text: "🟨" }

  puts "\n  ┌─ RRF FUSION RESULT (top #{hybrid_candidates.size}) ──────────────────────────────────────────┐"
  puts "  │                                                                              │"
  puts "  │  Formula: score(d) = 0.6 / (60 + rank_vec) + 0.4 / (60 + rank_txt)          │"
  puts "  │  Interleave: 🔗 both first → 🟦 70% vector → 🟨 30% text (guaranteed)       │"
  puts "  │                                                                              │"
  puts "  │  Source breakdown: 🔗 both=#{both}  🟦 vector=#{vec_only}  🟨 text=#{txt_only}#{" " * [ 1, 38 - both.to_s.length - vec_only.to_s.length - txt_only.to_s.length ].max}│"
  puts "  │                                                                              │"
  puts "  │  #{"#".rjust(3)}  #{"Name".ljust(24)} #{"Sim%".rjust(6)}   #{"RRF".rjust(8)}  #{"Source".ljust(12)}            │"
  puts "  │  #{"─" * 62}            │"

  hybrid_candidates.each_with_index do |c, i|
    icon = source_icons[c[:source]] || "?"
    src_label = c[:source].to_s.upcase
    rrf = c[:rrf_score] ? format("%.6f", c[:rrf_score]) : "  —"
    line = format("  %3d  %-24s %5.1f%%   %8s  %s %-8s", i + 1, c[:name].to_s.truncate(22), c[:similarity], rrf, icon, src_label)
    puts "  │#{line.ljust(76)}│"
  end

  puts "  │                                                                              │"
  puts "  └──────────────────────────────────────────────────────────────────────────────┘"
end

def print_results_comparison(original, final_results)
  puts "\n  What changed from the original search to the refined + hybrid search?"
  puts ""

  orig_ids = original.map { |c| c[:candidate_id] }.to_set
  final_ids = final_results.map { |c| c[:candidate_id] }.to_set

  new_ids = final_ids - orig_ids
  dropped_ids = orig_ids - final_ids
  kept_ids = orig_ids & final_ids

  orig_map = original.index_by { |c| c[:candidate_id] }
  final_map = final_results.index_by { |c| c[:candidate_id] }
  source_icons = { both: "🔗 BOTH", vector: "🟦 VEC", text: "🟨 TXT" }

  header = format("  %-4s %-24s %-10s %-10s %-8s %-10s %s", "#", "Name", "Before%", "After%", "Δ", "Source", "Status")
  puts header
  puts "  #{"─" * 82}"

  rows = []

  final_results.each_with_index do |c, i|
    orig = orig_map[c[:candidate_id]]
    delta = orig ? c[:similarity] - orig[:similarity] : nil
    src = source_icons[c[:source]] || "   —"

    status = if new_ids.include?(c[:candidate_id])
               c[:source] == :text ? "★ NEW (ES)" : "★ NEW (vec)"
    elsif delta && delta > 0.5
               "▲ IMPROVED"
    else
               "= KEPT"
    end

    rows << format("  %-4d %-24s %-10s %-10s %-8s %-10s %s",
      i + 1,
      c[:name].to_s.truncate(22),
      orig ? "#{orig[:similarity]}%" : "  —",
      "#{c[:similarity]}%",
      delta ? "%+.1f" % delta : " new",
      src,
      status
    )
  end

  dropped_ids.each do |id|
    orig = orig_map[id]
    next unless orig

    rows << format("  %-4s %-24s %-10s %-10s %-8s %-10s %s",
      "—",
      orig[:name].to_s.truncate(22),
      "#{orig[:similarity]}%",
      "  —",
      "  —",
      "   —",
      "✗ DROPPED"
    )
  end

  rows.each { |r| puts r }

  puts "  #{"─" * 82}"

  text_new = final_results.count { |c| c[:source] == :text && new_ids.include?(c[:candidate_id]) }
  vec_new = final_results.count { |c| c[:source] != :text && new_ids.include?(c[:candidate_id]) }

  puts "\n  Summary: ★ #{new_ids.size} new (#{text_new} from ES, #{vec_new} from vector) | ✗ #{dropped_ids.size} dropped | = #{kept_ids.size} kept"
end

def print_skill_scan(candidates, desired_skills)
  return if desired_skills.empty? || candidates.empty?

  source_icons = { both: "🔗", vector: "🟦", text: "🟨" }
  puts "\n  ┌─ SKILL PRESENCE IN TOP RESULTS ─────────────────────────────────────────────┐"

  candidates.take(10).each do |cand|
    full_text = build_full_text(cand)
    matched = desired_skills.select { |ds| full_text.include?(ds.downcase) }
    missing = desired_skills - matched

    match_pct = desired_skills.size > 0 ? (matched.size.to_f / desired_skills.size * 100).round(0) : 0
    bar = progress_bar(match_pct, 100, 12)

    verdict = match_pct == 100 ? "PERFECT ✓" : match_pct > 0 ? "PARTIAL" : "NO MATCH"
    src = source_icons[cand[:source]] || "  "

    puts "  │  #{src} %-18s %5.1f%% %s %3d%% %-10s│" % [ cand[:name].to_s.truncate(16), cand[:similarity], bar, match_pct, verdict ]
    puts "  │     ✓ matched: #{matched.join(", ").truncate(60).ljust(62)}│" if matched.any?
    puts "  │     ✗ missing: #{missing.join(", ").truncate(60).ljust(62)}│" if missing.any?
  end

  puts "  └──────────────────────────────────────────────────────────────────────────────┘"
end

def print_final_verdict(original, vectorial, hybrid, intent_result)
  puts ""
  puts "  ╔#{"═" * (PHASE_WIDTH - 4)}╗"
  puts "  ║#{"FINAL VERDICT".center(PHASE_WIDTH - 4)}║"
  puts "  ╠#{"═" * (PHASE_WIDTH - 4)}╣"

  print_verdict_line("1. Vectorial Refinement (α=0.3, β=0.2)", true, "Centroid adjusted towards likes, away from dislikes")

  if intent_result[:worked]
    print_verdict_line("2. Intent Extraction (Gemini 2.5 Flash)", true, "LLM → description + ES query + skill classification")
  else
    print_verdict_line("2. Intent Extraction", false, "All feedback NOT_SEARCHABLE or no feedback")
  end

  if intent_result[:es_query].present? && hybrid.any?
    both = hybrid.count { |c| c[:source] == :both }
    vec = hybrid.count { |c| c[:source] == :vector }
    txt = hybrid.count { |c| c[:source] == :text }
    detail = "Top #{hybrid.size}: #{both} both + #{vec} vector + #{txt} text"
    print_verdict_line("3. Hybrid Search (RRF fusion)", true, detail)
  else
    print_verdict_line("3. Hybrid Search (RRF fusion)", false, "No ES query → vector-only results")
  end

  original_ids = original.map { |c| c[:candidate_id] }.to_set
  final = hybrid.presence || vectorial.first(10)
  new_count = final.count { |c| !original_ids.include?(c[:candidate_id]) }
  text_new = final.count { |c| c[:source] == :text && !original_ids.include?(c[:candidate_id]) }

  puts "  ║#{" " * (PHASE_WIDTH - 4)}║"
  if new_count > 0
    impact = "#{new_count} NEW candidates surfaced"
    impact += " (#{text_new} from ES)" if text_new > 0
    print_verdict_line("4. Impact", true, impact)
  else
    print_verdict_line("4. Impact", false, "No new candidates — may need more/different feedback")
  end

  puts "  ║#{" " * (PHASE_WIDTH - 4)}║"
  puts "  ╚#{"═" * (PHASE_WIDTH - 4)}╝"
end

def print_verdict_line(label, success, detail)
  icon = success ? "✅" : "⚠️ "
  line = "  #{icon} #{label}"
  puts "  ║  #{line.ljust(PHASE_WIDTH - 7)}║"
  puts "  ║     #{detail.truncate(PHASE_WIDTH - 12).ljust(PHASE_WIDTH - 9)}║"
end

def build_desired_skills(intent_result)
  skills = intent_result[:desired_skills].dup
  skills += intent_result[:must_have] if intent_result[:must_have]
  skills += intent_result[:searchable] if intent_result[:searchable]
  skills.uniq
end

def extract_desired_skills_from_feedback(feedbacks)
  skills = []
  feedbacks.each do |fb|
    reason = fb[:reason].to_s.downcase
    reason.scan(/(?:não sabe|nao sabe|não conhece|nao conhece|falta|sem)\s+(\w[\w\s]*)/i).each do |match|
      skills << match[0].strip
    end
  end
  skills.uniq
end

def word_wrap(text, max_width)
  words = text.to_s.split
  lines = []
  current = ""
  words.each do |word|
    if (current + " " + word).strip.length > max_width
      lines << current.strip unless current.strip.empty?
      current = word
    else
      current = current.empty? ? word : "#{current} #{word}"
    end
  end
  lines << current.strip unless current.strip.empty?
  lines
end

def search_candidates(centroid, exclude_ids, threshold, limit, account)
  return [] unless centroid

  results = Embedding
    .where(reference_type: "Candidate")
    .where.not(reference_id: exclude_ids)
    .nearest_neighbors(:embedding, centroid, distance: "cosine")
    .limit(limit * 3)

  tenant_ids = Candidate
    .where(account_id: account.id, is_deleted: false)
    .where(id: results.map(&:reference_id))
    .pluck(:id)
    .to_set

  candidates_map = Candidate.where(id: tenant_ids).index_by(&:id)

  results
    .select { |emb| tenant_ids.include?(emb.reference_id) }
    .filter_map do |emb|
      similarity = (1.0 - emb.neighbor_distance).clamp(0.0, 1.0)
      next if similarity < threshold

      cand = candidates_map[emb.reference_id]
      next unless cand

      {
        candidate_id: emb.reference_id,
        similarity: (similarity * 100).round(1),
        name: cand.name,
        role: cand.role_name,
        skills: extract_demo_skills(cand),
        source: :vector
      }
    end
    .first(limit)
end

def extract_demo_skills(candidate)
  skills = []

  if candidate.respond_to?(:data_raw) && candidate.data_raw.is_a?(Hash)
    raw = candidate.data_raw.dig("skills") || []
    skills.concat(raw.map { |s| s.is_a?(Hash) ? s["name"] : s }.compact)
  end

  if candidate.respond_to?(:curriculum_text) && candidate.curriculum_text.present?
    text = candidate.curriculum_text.downcase
    %w[ruby rails python java javascript typescript react node spring django api rest graphql
       sql postgresql mysql mongodb redis docker kubernetes aws azure gcp].each do |s|
      skills << s if text.include?(s)
    end
  end

  skills.uniq.compact
end

def build_demo_exclude_ids(context)
  ids = context[:base_candidate_ids].dup
  ids += context[:liked_ids]
  ids += context[:disliked_feedbacks].map { |d| d[:candidate_id] }
  ids.uniq
end

def build_full_text(candidate_or_hash)
  cand = if candidate_or_hash.is_a?(Hash)
           Candidate.find_by(id: candidate_or_hash[:candidate_id])
  else
           candidate_or_hash
  end
  return "" unless cand

  skills = extract_demo_skills(cand).join(" ")
  "#{skills} #{cand.curriculum_text}".downcase
end

def progress_bar(value, max, width)
  filled = [ (value / max * width).round, width ].min
  "▓" * filled + "░" * (width - filled)
end

def cosine_sim(vec1, vec2)
  dot = 0.0
  m1 = 0.0
  m2 = 0.0
  vec1.each_with_index do |a, i|
    b = vec2[i].to_f
    dot += a * b
    m1 += a * a
    m2 += b * b
  end
  return 0.0 if m1.zero? || m2.zero?

  (dot / (Math.sqrt(m1) * Math.sqrt(m2))).clamp(-1.0, 1.0)
end

def centroid_shift_pct(original, refined)
  sim = cosine_sim(original, refined)
  ((1 - sim) * 100).round(4)
end

refinement_visual_demo if __FILE__ == $PROGRAM_NAME || (caller.length == 1 && caller[0].include?("rails/commands/runner"))
