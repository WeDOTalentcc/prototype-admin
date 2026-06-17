# frozen_string_literal: true

class RefinementQualityAnalyzerV2
  ALPHA = 0.3
  BETA = 0.2

  def initialize(sourcing_id, use_llm: true, test_intent_blending: true)
    @sourcing = Sourcing.find(sourcing_id)
    @account_id = @sourcing.account_id
    @use_llm = use_llm
    @test_intent_blending = test_intent_blending
    @desired_skills = []
  end

  def full_report
    print_header("🔬 REFINEMENT QUALITY ANALYSIS V2")

    step_1_context
    step_2_parse_feedback_intent
    step_3_dual_search_comparison
    step_4_curriculum_deep_scan
    step_5_verdict

    print_separator
    puts "✅ Analysis complete!"
  end

  private

  def step_1_context
    print_section("STEP 1: SEARCH CONTEXT")

    base_ids = @sourcing.parameters["base_candidate_ids"]
    @base_candidates = Candidate.where(id: base_ids, account_id: @account_id)

    puts "\n  👥 BASE CANDIDATES:"
    @base_candidates.each do |cand|
      puts "    • #{cand.name} (ID: #{cand.id})"
      puts "      Role: #{cand.role_name || 'N/A'}"
      skills = extract_skills(cand)
      puts "      Skills: #{skills.take(8).join(', ')}" if skills.any?
    end

    @likes = CandidateFeedback.where(sourcing_id: @sourcing.id, feedback_type: "like").includes(:candidate)
    @dislikes = CandidateFeedback.where(sourcing_id: @sourcing.id, feedback_type: "dislike").includes(:candidate)

    puts "\n  ✅ LIKES (#{@likes.count}):"
    @likes.each do |fb|
      puts "    • #{fb.candidate&.name} (ID: #{fb.candidate_id})"
    end

    puts "\n  ❌ DISLIKES (#{@dislikes.count}):"
    @dislikes.each do |fb|
      puts "    • #{fb.candidate&.name} (ID: #{fb.candidate_id})"
      puts "      Reason: \"#{fb.reason}\""
    end
  end

  def step_2_parse_feedback_intent
    print_section("STEP 2: FEEDBACK INTENT ANALYSIS (LLM-powered)")

    return if @dislikes.empty?

    dislike_reasons = @dislikes.map(&:reason).compact

    @desired_skills = @use_llm ? extract_desired_skills_with_llm(dislike_reasons) : fallback_skill_extraction(dislike_reasons)

    if @desired_skills.any?
      puts "\n  🎯 RECRUITER WANTS candidates with:"
      @desired_skills.each { |skill| puts "    → #{skill}" }

      puts "\n  ⚠️  NOTE: Current vectorial refinement does NOT parse these."
      puts "     It only moves AWAY from rejected candidates' embeddings."
      puts "     For skill-based matching, we need hybrid search or query expansion."
    else
      puts "\n  No specific skills extracted from feedback."
    end
  end

  def step_3_dual_search_comparison
    print_section("STEP 3: ORIGINAL vs REFINED SEARCH (Side-by-Side)")

    base_ids = @sourcing.parameters["base_candidate_ids"]
    @original_centroid = compute_centroid(base_ids)

    return unless @original_centroid

    liked_ids = @likes.pluck(:candidate_id)
    disliked_ids = @dislikes.pluck(:candidate_id)

    service = Candidates::SimilarCandidates::EmbeddingRefinementService.new(
      original_centroid: @original_centroid
    )

    @refined_centroid = service.refine(
      liked_ids: liked_ids,
      disliked_ids: disliked_ids
    )

    cos_sim = cosine_similarity(@original_centroid, @refined_centroid)
    shift_pct = ((1 - cos_sim) * 100).round(4)

    puts "\n  📐 Vector Shift (Vectorial only): #{shift_pct}% divergence (similarity: #{(cos_sim * 100).round(2)}%)"

    if shift_pct < 0.1
      puts "  ⚠️  MINIMAL SHIFT - rejected candidates too similar to base"
    elsif shift_pct < 1.0
      puts "  ✅ MODERATE SHIFT - some reranking expected"
    else
      puts "  ✅ SIGNIFICANT SHIFT - results should differ noticeably"
    end

    if @test_intent_blending && @dislikes.any?
      puts "\n  🧠 Testing INTENT-BASED BLENDING..."

      disliked_feedbacks = @dislikes.map do |fb|
        { candidate_id: fb.candidate_id, candidate: fb.candidate, reason: fb.reason }
      end

      liked_candidates = Candidate.where(id: liked_ids, account_id: @account_id)
      base_candidates = Candidate.where(id: base_ids, account_id: @account_id)

      intent_service = Candidates::SimilarCandidates::IntentBasedRefinementService.new
      @intent_refined_centroid = intent_service.refine_with_intent(
        original_centroid: @original_centroid,
        vectorial_refined: @refined_centroid,
        base_candidates: base_candidates,
        disliked_feedbacks: disliked_feedbacks,
        liked_candidates: liked_candidates
      )

      intent_cos_sim = cosine_similarity(@original_centroid, @intent_refined_centroid)
      intent_shift_pct = ((1 - intent_cos_sim) * 100).round(4)

      puts "  📐 Vector Shift (Intent-blended): #{intent_shift_pct}% divergence (similarity: #{(intent_cos_sim * 100).round(2)}%)"

      vectorial_vs_intent = cosine_similarity(@refined_centroid, @intent_refined_centroid)
      intent_diff = ((1 - vectorial_vs_intent) * 100).round(4)

      puts "  📊 Vectorial vs Intent difference: #{intent_diff}%"
    end

    existing_ids = SourcedProfileSourcing
      .joins(:sourced_profile)
      .where(sourcing_id: @sourcing.id, is_deleted: false)
      .pluck("sourced_profiles.candidate_id")

    exclude_ids = (base_ids + liked_ids + disliked_ids + existing_ids).uniq
    threshold = @sourcing.search_metadata&.dig("threshold") || 0.40  # Lowered for testing
    limit = 30

    puts "\n  🔍 Running ORIGINAL centroid search..."
    @original_results = run_vector_search(@original_centroid, exclude_ids, threshold, limit)

    puts "  🔍 Running VECTORIAL REFINED centroid search..."
    @refined_results = run_vector_search(@refined_centroid, exclude_ids, threshold, limit)

    if @intent_refined_centroid
      puts "  🔍 Running INTENT-BLENDED centroid search..."
      @intent_refined_results = run_vector_search(@intent_refined_centroid, exclude_ids, threshold, limit)
      puts "\n  Results: #{@original_results.size} original, #{@refined_results.size} vectorial, #{@intent_refined_results.size} intent-blended"
    else
      puts "\n  Results: #{@original_results.size} original, #{@refined_results.size} refined"
    end

    build_comparison_table
  end

  def step_4_curriculum_deep_scan
    print_section("STEP 4: CURRICULUM SCAN FOR DESIRED SKILLS")

    if @desired_skills.empty?
      puts "\n  No desired skills to scan for."
      return
    end

    puts "\n  Scanning top results for: #{@desired_skills.join(', ')}"

    if @intent_refined_results
      top_intent = @comparison&.select { |r| r[:intent_score] }&.take(15) || []

      if top_intent.any?
        puts "\n  📋 INTENT-BLENDED RESULTS:"
        @curriculum_matches = scan_curriculums(top_intent)
        print_curriculum_matches
      end
    else
      top_refined = @comparison&.select { |r| r[:ref_score] }&.take(15) || []

      if top_refined.any?
        @curriculum_matches = scan_curriculums(top_refined)
        print_curriculum_matches
      else
        puts "\n  ⚠️  No refined results to scan"
      end
    end
  end

  def step_5_verdict
    print_section("STEP 5: FINAL VERDICT")

    puts "\n  A) VECTOR ADJUSTMENT:"

    if @original_centroid && @refined_centroid
      cos_sim = cosine_similarity(@original_centroid, @refined_centroid)
      shift = ((1 - cos_sim) * 100).round(4)

      if shift < 0.1
        puts "    ❌ MINIMAL (#{shift}% shift) - vector barely moved"
        puts "       Rejected candidates have similar embeddings to base"
      elsif shift < 1.0
        puts "    ⚠️  MODERATE (#{shift}% shift) - some adjustment"
      else
        puts "    ✅ SIGNIFICANT (#{shift}% shift) - clear movement"
      end
    end

    puts "\n  B) SKILL MATCHING:"

    if @curriculum_matches && @desired_skills.any?
      total = @curriculum_matches.size
      with_skills = @curriculum_matches.count { |m| m[:matched_any] }
      pct = total > 0 ? ((with_skills.to_f / total) * 100).round(1) : 0

      puts "    #{with_skills}/#{total} (#{pct}%) have desired skills"

      if pct > 60
        puts "    ✅ EFFECTIVE - most results match intent"
      elsif pct > 30
        puts "    ⚠️  PARTIAL - some matches but inconsistent"
      else
        puts "    ❌ INEFFECTIVE - skills not being surfaced"
        puts "\n    ROOT CAUSE: Vectorial refinement is blind to textual feedback."
        puts "    System moves away from rejected embedding, not towards desired skills."
      end
    end

    puts "\n  C) RECOMMENDATIONS:"

    if @desired_skills.any? && (@curriculum_matches&.count { |m| m[:matched_any] } || 0).to_f / [ @curriculum_matches&.size || 1, 1 ].max < 0.4
      puts "    To improve skill-based refinement:"
      puts "    1. LLM Query Expansion: Use Gemini to generate search query from feedback"
      puts "    2. Hybrid Search: Combine vector similarity + Elasticsearch keyword match"
      puts "    3. Skill Embedding: Generate embedding from desired skills and blend into centroid"
      puts "    4. Post-filtering: Boost/filter results based on extracted skills"
    else
      puts "    Current approach appears adequate for this scenario."
    end
  end

  def extract_desired_skills_with_llm(dislike_reasons)
    return [] if dislike_reasons.empty?

    prompt = build_skill_extraction_prompt(dislike_reasons)

    begin
      response = call_gemini_api(prompt)
      parsed = JSON.parse(response)
      Array(parsed["desired_skills"]).compact.uniq
    rescue => e
      Rails.logger.warn "[RefinementAnalyzer] LLM extraction failed: #{e.message}"
      fallback_skill_extraction(dislike_reasons)
    end
  end

  def build_skill_extraction_prompt(reasons)
    <<~PROMPT
      You are analyzing recruiter feedback to understand what skills they want in candidates.

      When a recruiter says "não sabe X" or "nao sabe X", it means the rejected candidate#{' '}
      LACKS skill X, so the recruiter WANTS candidates WITH skill X.

      Rejection reasons:
      #{reasons.map.with_index { |r, i| "#{i + 1}. #{r}" }.join("\n")}

      Extract the desired skills/technologies the recruiter is looking for.

      Respond ONLY with valid JSON in this format:
      {
        "desired_skills": ["skill1", "skill2", ...]
      }

      Examples:
      - "não sabe rails" → wants "rails"
      - "nao conhece react" → wants "react"
      - "muito junior" → NOT a skill, ignore
      - "precisa saber kubernetes" → wants "kubernetes"
    PROMPT
  end

  def call_gemini_api(prompt)
    require 'net/http'
    require 'json'

    api_key = ENV.fetch('GEMINI_API_KEY', nil)
    return nil unless api_key

    model = ENV.fetch('GEMINI_FAST_MODEL', 'gemini-2.5-flash')
    uri = URI("https://generativelanguage.googleapis.com/v1beta/models/#{model}:generateContent?key=#{api_key}")

    request = Net::HTTP::Post.new(uri)
    request['Content-Type'] = 'application/json'
    request.body = {
      contents: [ {
        parts: [ { text: prompt } ]
      } ],
      generationConfig: {
        temperature: 0.1,
        maxOutputTokens: 500
      }
    }.to_json

    response = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) do |http|
      http.request(request)
    end

    result = JSON.parse(response.body)
    result.dig('candidates', 0, 'content', 'parts', 0, 'text')
  rescue => e
    Rails.logger.error "[RefinementAnalyzer] Gemini API error: #{e.message}"
    nil
  end

  def fallback_skill_extraction(reasons)
    skills = []

    reasons.each do |reason|
      reason_lower = reason.downcase

      patterns = [
        /n[aã]o\s+sabe\s+(\w+)/,
        /nao\s+sabe\s+(\w+)/,
        /n[aã]o\s+conhece\s+(\w+)/,
        /precisa\s+(?:de\s+)?(\w+)/,
        /needs?\s+(\w+)/,
        /falta\s+(\w+)/
      ]

      patterns.each do |pat|
        if match = reason_lower.match(pat)
          skill = match[1].strip
          skills << skill unless skill.length < 3
        end
      end
    end

    skills.uniq
  end

  def build_comparison_table
    return unless @original_results && @refined_results

    orig_map = @original_results.each_with_index.to_h { |r, i| [ r[:candidate_id], { score: r[:score], rank: i + 1 } ] }
    ref_map = @refined_results.each_with_index.to_h { |r, i| [ r[:candidate_id], { score: r[:score], rank: i + 1 } ] }
    intent_map = @intent_refined_results&.each_with_index&.to_h { |r, i| [ r[:candidate_id], { score: r[:score], rank: i + 1 } ] } || {}

    all_ids = (orig_map.keys + ref_map.keys + intent_map.keys).uniq
    candidates = Candidate.where(id: all_ids, account_id: @account_id).index_by(&:id)

    @comparison = all_ids.map do |cid|
      cand = candidates[cid]
      orig = orig_map[cid]
      ref = ref_map[cid]
      intent = intent_map[cid]

      orig_score = orig ? (orig[:score] * 100).round(1) : nil
      ref_score = ref ? (ref[:score] * 100).round(1) : nil
      intent_score = intent ? (intent[:score] * 100).round(1) : nil

      delta_ref = (orig_score && ref_score) ? (ref_score - orig_score).round(1) : nil
      delta_intent = (orig_score && intent_score) ? (intent_score - orig_score).round(1) : nil

      status = if intent
                 if intent_score && orig_score && (intent_score - orig_score) > 1.0
                   :intent_improved
                 elsif orig.nil?
                   :new
                 else
                   :stable
                 end
      elsif orig.nil? && ref
                 :new
      elsif orig && ref.nil?
                 :dropped
      elsif delta_ref && delta_ref > 0.5
                 :improved
      elsif delta_ref && delta_ref < -0.5
                 :declined
      else
                 :stable
      end

      {
        candidate_id: cid,
        candidate: cand,
        name: cand&.name || "Unknown",
        role: cand&.role_name || "",
        orig_score: orig_score,
        ref_score: ref_score,
        intent_score: intent_score,
        delta_ref: delta_ref,
        delta_intent: delta_intent,
        orig_rank: orig&.dig(:rank),
        ref_rank: ref&.dig(:rank),
        intent_rank: intent&.dig(:rank),
        status: status
      }
    end

    @comparison.sort_by! { |c| -(c[:intent_score] || c[:ref_score] || c[:orig_score] || 0) }

    puts "\n  📊 COMPARISON TABLE:"
    puts "  " + "─" * 120

    if @intent_refined_results
      puts "  %-6s %-25s %-8s %-8s %-8s %-8s %-8s %s" % [ "ID", "Name", "Orig%", "Vec%", "Intent%", "ΔVec", "ΔInt", "Status" ]
    else
      puts "  %-6s %-30s %-8s %-8s %-8s %-8s %s" % [ "ID", "Name", "Orig%", "Ref%", "Δ", "Status", "Ranks" ]
    end

    puts "  " + "─" * 120

    @comparison.take(20).each do |row|
      if @intent_refined_results
        delta_ref_str = row[:delta_ref] ? "%+.1f" % row[:delta_ref] : "-"
        delta_intent_str = row[:delta_intent] ? "%+.1f" % row[:delta_intent] : "-"

        status_icon = case row[:status]
        when :intent_improved then "🎯"
        when :improved then "▲"
        when :declined then "▼"
        when :new then "★"
        when :dropped then "✗"
        else "="
        end

        puts "  %-6d %-25s %-8s %-8s %-8s %-8s %-8s %s" % [
          row[:candidate_id],
          row[:name].to_s.truncate(23),
          row[:orig_score] ? "#{row[:orig_score]}%" : "-",
          row[:ref_score] ? "#{row[:ref_score]}%" : "-",
          row[:intent_score] ? "#{row[:intent_score]}%" : "-",
          delta_ref_str,
          delta_intent_str,
          "#{status_icon} #{row[:status]}"
        ]
      else
        delta_str = row[:delta_ref] ? "%+.1f" % row[:delta_ref] : "-"
        status_icon = case row[:status]
        when :improved then "▲"
        when :declined then "▼"
        when :new then "★"
        when :dropped then "✗"
        else "="
        end

        ranks = "#{row[:orig_rank] || '-'} → #{row[:ref_rank] || '-'}"

        puts "  %-6d %-30s %-8s %-8s %-8s %-8s %s" % [
          row[:candidate_id],
          row[:name].to_s.truncate(28),
          row[:orig_score] ? "#{row[:orig_score]}%" : "-",
          row[:ref_score] ? "#{row[:ref_score]}%" : "-",
          delta_str,
          "#{status_icon} #{row[:status]}",
          ranks
        ]
      end
    end
    puts "  " + "─" * 120

    if @intent_refined_results
      stats = @comparison.group_by { |r| r[:status] }.transform_values(&:count)
      puts "\n  Stats: 🎯 #{stats[:intent_improved] || 0} intent-improved | ★ #{stats[:new] || 0} new | = #{stats[:stable] || 0} stable"
    else
      stats = @comparison.group_by { |r| r[:status] }.transform_values(&:count)
      puts "\n  Stats: ▲ #{stats[:improved] || 0} improved | ▼ #{stats[:declined] || 0} declined | ★ #{stats[:new] || 0} new | ✗ #{stats[:dropped] || 0} dropped"
    end
  end

  def scan_curriculums(top_results)
    matches = []

    top_results.each do |row|
      cand = row[:candidate]
      next unless cand

      curriculum = build_curriculum_text(cand)
      curriculum_lower = curriculum.downcase

      skill_matches = {}
      matched_any = false

      @desired_skills.each do |skill|
        skill_lower = skill.downcase.strip
        patterns = build_skill_patterns(skill_lower)

        found = patterns.any? { |pat| curriculum_lower.match?(pat) }
        skill_matches[skill] = found
        matched_any = true if found
      end

      matches << {
        candidate_id: row[:candidate_id],
        name: row[:name],
        role: row[:role],
        ref_score: row[:intent_score] || row[:ref_score],
        matches: skill_matches,
        matched_any: matched_any,
        curriculum: curriculum
      }
    end

    matches
  end

  def build_curriculum_text(candidate)
    parts = []

    parts << candidate.curriculum_text if candidate.curriculum_text.present?
    parts << candidate.role_name if candidate.role_name.present?
    parts << candidate.headline if candidate.respond_to?(:headline) && candidate.headline.present?
    parts << extract_skills(candidate).join(" ")

    parts.join(" | ")
  end

  def build_skill_patterns(skill)
    base = [ Regexp.new("\\b#{Regexp.escape(skill)}\\b", Regexp::IGNORECASE) ]

    variants = case skill
    when "ruby"
                 [ /\bruby\s+on\s+rails\b/i, /\bror\b/i, /\brubyist\b/i ]
    when "rails"
                 [ /\bruby\s+on\s+rails\b/i, /\brails\s+\d/i, /\bror\b/i ]
    when "react"
                 [ /\breactjs\b/i, /\breact\.js\b/i, /\breact\s+native\b/i ]
    when "node"
                 [ /\bnodejs\b/i, /\bnode\.js\b/i ]
    when "python"
                 [ /\bpython\s+\d/i, /\bpythonista\b/i ]
    else
                 []
    end

    base + variants
  end

  def print_curriculum_matches
    return unless @curriculum_matches

    puts "\n  📋 SKILL PRESENCE IN TOP RESULTS:"
    puts "  " + "─" * 110

    skill_headers = @desired_skills.map { |s| s.truncate(12).ljust(12) }.join(" ")
    puts "  %-6s %-25s %-8s | %s | %s" % [ "ID", "Name", "Score", skill_headers, "Verdict" ]
    puts "  " + "─" * 110

    @curriculum_matches.each do |row|
      skill_cols = @desired_skills.map do |skill|
        row[:matches][skill] ? "✓".ljust(12) : "✗".ljust(12)
      end.join(" ")

      verdict = if row[:matches].values.all?
                  "PERFECT"
      elsif row[:matched_any]
                  "PARTIAL"
      else
                  "NO MATCH"
      end

      puts "  %-6d %-25s %-8s | %s | %s" % [
        row[:candidate_id],
        row[:name].to_s.truncate(23),
        "#{row[:ref_score]}%",
        skill_cols,
        verdict
      ]
    end
    puts "  " + "─" * 110

    total = @curriculum_matches.size
    perfect = @curriculum_matches.count { |r| r[:matches].values.all? }
    partial = @curriculum_matches.count { |r| r[:matched_any] && !r[:matches].values.all? }
    none = @curriculum_matches.count { |r| !r[:matched_any] }

    puts "\n  Perfect: #{perfect}/#{total} | Partial: #{partial}/#{total} | None: #{none}/#{total}"

    print_curriculum_excerpts
  end

  def print_curriculum_excerpts
    puts "\n  📄 CURRICULUM EXCERPTS (top 5 with highlights):"
    puts ""

    @curriculum_matches.take(5).each do |row|
      puts "  #{row[:name]} (#{row[:ref_score]}%)"
      puts "  #{row[:role].truncate(60)}"

      excerpt = row[:curriculum].truncate(250)

      @desired_skills.each do |skill|
        excerpt = excerpt.gsub(/\b(#{Regexp.escape(skill)})\b/i, "\e[42m\e[30m\\1\e[0m")
      end

      puts "  #{excerpt}"
      puts "  " + "─" * 80
      puts ""
    end
  end

  def compute_centroid(candidate_ids)
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

  def run_vector_search(centroid, exclude_ids, threshold, limit)
    return [] unless centroid

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
    results.map { |row| { candidate_id: row['reference_id'].to_i, score: row['similarity'].to_f } }
  rescue => e
    Rails.logger.error "[RefinementAnalyzer] Search error: #{e.message}"
    []
  end

  def cosine_similarity(vec1, vec2)
    dot_product = vec1.zip(vec2).sum { |a, b| a * b }
    mag1 = Math.sqrt(vec1.sum { |v| v**2 })
    mag2 = Math.sqrt(vec2.sum { |v| v**2 })

    return 0.0 if mag1.zero? || mag2.zero?

    dot_product / (mag1 * mag2)
  end

  def extract_skills(candidate)
    skills = []

    if candidate.respond_to?(:data_raw) && candidate.data_raw.is_a?(Hash)
      raw_skills = candidate.data_raw.dig("skills") || []
      skills.concat(raw_skills.map { |s| s.is_a?(Hash) ? s["name"] : s }.compact)
    end

    if candidate.respond_to?(:curriculum_text) && candidate.curriculum_text.present?
      text = candidate.curriculum_text.downcase
      common_skills = %w[ruby rails python java javascript typescript react node api rest sql postgresql mysql mongodb redis docker kubernetes aws azure gcp agile scrum]

      common_skills.each do |skill|
        skills << skill if text.include?(skill)
      end
    end

    skills.uniq.compact
  end

  def print_header(text)
    puts "\n"
    puts "=" * 80
    puts text.center(80)
    puts "=" * 80
    puts "\n"
  end

  def print_section(title)
    puts "\n"
    puts "━" * 80
    puts "#{title}"
    puts "━" * 80
  end

  def print_separator
    puts "\n" + "─" * 80
  end
end

puts "🔬 Refinement Quality Analyzer V2 loaded!"
puts ""
puts "Usage:"
puts "  analyzer = RefinementQualityAnalyzerV2.new(sourcing_id)"
puts "  analyzer.full_report"
puts ""
puts "Features:"
puts "  ✅ LLM-powered feedback parsing (extracts desired skills)"
puts "  ✅ Side-by-side comparison (original vs refined search)"
puts "  ✅ Curriculum deep scan (finds skills in candidate text)"
puts "  ✅ Comprehensive verdict with recommendations"
puts ""
puts "Example:"
puts "  analyzer = RefinementQualityAnalyzerV2.new(564)"
puts "  analyzer.full_report"
