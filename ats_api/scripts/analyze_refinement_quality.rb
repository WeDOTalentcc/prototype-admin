# frozen_string_literal: true

class RefinementQualityAnalyzer
  def initialize(sourcing_id)
    @sourcing = Sourcing.find(sourcing_id)
    @account_id = @sourcing.account_id
  end

  def analyze
    print_header("🔍 SIMILARITY SEARCH REFINEMENT ANALYSIS")

    print_sourcing_info
    print_base_candidates
    print_feedbacks
    print_refinement_simulation
    print_validation_results

    print_separator
    puts "✅ Analysis complete!"
  end

  private

  def print_sourcing_info
    print_section("📊 SOURCING INFO")
    puts "  ID: #{@sourcing.id}"
    puts "  Query: #{@sourcing.query}"
    puts "  Status: #{@sourcing.status}"
    puts "  Results: #{@sourcing.results_count} candidates"
    puts "  Created: #{@sourcing.created_at.strftime('%Y-%m-%d %H:%M')}"
  end

  def print_base_candidates
    print_section("👥 BASE CANDIDATES (Reference)")

    base_ids = @sourcing.parameters["base_candidate_ids"]
    base_candidates = Candidate.where(id: base_ids, account_id: @account_id)

    base_candidates.each do |candidate|
      puts "\n  🧑 #{candidate.name} (ID: #{candidate.id})"
      puts "     Role: #{candidate.role_name || 'N/A'}"
      puts "     Company: #{candidate.current_company || 'N/A'}"

      skills = extract_skills(candidate)
      if skills.any?
        puts "     Top Skills: #{skills.take(10).join(', ')}"
      else
        puts "     Skills: No skills extracted"
      end
    end
  end

  def print_feedbacks
    print_section("👍👎 CANDIDATE FEEDBACKS")

    feedbacks = CandidateFeedback
      .where(sourcing_id: @sourcing.id)
      .includes(:candidate)
      .order(created_at: :asc)

    if feedbacks.empty?
      puts "  ⚠️  No feedbacks recorded yet"
      return
    end

    likes = feedbacks.where(feedback_type: "like")
    dislikes = feedbacks.where(feedback_type: "dislike")

    if likes.any?
      puts "\n  ✅ LIKES (#{likes.count}):"
      likes.each do |fb|
        candidate = fb.candidate
        puts "\n    • #{candidate.name} (ID: #{candidate.id})"
        puts "      Role: #{candidate.role_name || 'N/A'}"
        skills = extract_skills(candidate)
        puts "      Skills: #{skills.take(8).join(', ')}" if skills.any?
      end
    end

    if dislikes.any?
      puts "\n  ❌ DISLIKES (#{dislikes.count}):"
      dislikes.each do |fb|
        candidate = fb.candidate
        puts "\n    • #{candidate.name} (ID: #{candidate.id})"
        puts "      Role: #{candidate.role_name || 'N/A'}"
        puts "      Reason: \"#{fb.reason}\""
        skills = extract_skills(candidate)
        puts "      Skills: #{skills.take(8).join(', ')}" if skills.any?
      end
    end
  end

  def print_refinement_simulation
    print_section("🔄 REFINEMENT SIMULATION")

    feedbacks = CandidateFeedback.where(sourcing_id: @sourcing.id)

    if feedbacks.empty?
      puts "  ⚠️  Cannot simulate: no feedbacks available"
      return
    end

    liked_ids = feedbacks.where(feedback_type: "like").pluck(:candidate_id)
    disliked_ids = feedbacks.where(feedback_type: "dislike").pluck(:candidate_id)

    puts "  Liked candidates: #{liked_ids.count}"
    puts "  Disliked candidates: #{disliked_ids.count}"

    base_ids = @sourcing.parameters["base_candidate_ids"]
    original_centroid = compute_centroid(base_ids)

    if original_centroid.nil?
      puts "  ❌ Cannot compute original centroid (missing embeddings)"
      return
    end

    puts "\n  📐 Vector adjustment:"
    puts "     Alpha (like weight): 0.3"
    puts "     Beta (dislike weight): 0.2"

    service = Candidates::SimilarCandidates::EmbeddingRefinementService.new(
      original_centroid: original_centroid
    )

    refined_centroid = service.refine(
      liked_ids: liked_ids,
      disliked_ids: disliked_ids
    )

    cosine_change = cosine_similarity(original_centroid, refined_centroid)
    puts "     Cosine similarity (original vs refined): #{(cosine_change * 100).round(2)}%"

    @refined_centroid = refined_centroid
    @original_centroid = original_centroid
  end

  def print_validation_results
    print_section("✅ VALIDATION RESULTS")

    return unless @refined_centroid

    feedbacks = CandidateFeedback.where(sourcing_id: @sourcing.id)
    disliked_ids = feedbacks.where(feedback_type: "dislike").pluck(:candidate_id)
    disliked_reasons = feedbacks.where(feedback_type: "dislike").pluck(:reason).compact

    existing_candidate_ids = SourcedProfileSourcing
      .joins(:sourced_profile)
      .where(sourcing_id: @sourcing.id, is_deleted: false)
      .pluck("sourced_profiles.candidate_id")

    threshold = @sourcing.search_metadata&.dig("threshold") || 0.60

    puts "  🔍 Searching with refined vector..."
    puts "     Threshold: #{(threshold * 100).round(0)}%"
    puts "     Excluding: #{existing_candidate_ids.count} existing + #{disliked_ids.count} disliked"

    new_candidates = search_with_embedding(
      @refined_centroid,
      exclude_ids: existing_candidate_ids + disliked_ids,
      threshold: threshold,
      limit: 20
    )

    if new_candidates.empty?
      puts "\n  ⚠️  No new candidates found with refined vector"
      return
    end

    puts "\n  📋 FOUND #{new_candidates.count} NEW CANDIDATES:"

    new_candidates.take(10).each_with_index do |result, idx|
      candidate = result[:candidate]
      score = result[:score]

      puts "\n  #{idx + 1}. #{candidate.name} (ID: #{candidate.id})"
      puts "     Similarity: #{(score * 100).round(1)}%"
      puts "     Role: #{candidate.role_name || 'N/A'}"

      skills = extract_skills(candidate)
      puts "     Skills: #{skills.take(8).join(', ')}" if skills.any?

      if disliked_reasons.any?
        validate_against_dislikes(candidate, disliked_reasons, skills)
      end
    end

    analyze_skill_patterns(new_candidates, disliked_reasons)
  end

  def validate_against_dislikes(candidate, disliked_reasons, candidate_skills)
    disliked_reasons.each do |reason|
      reason_lower = reason.downcase

      if reason_lower.include?("não sabe") || reason_lower.include?("nao sabe")
        missing_skill = extract_missing_skill(reason_lower)

        if missing_skill
          has_skill = candidate_skills.any? { |s| s.downcase.include?(missing_skill) }

          if has_skill
            puts "     ✅ Has '#{missing_skill}' (recruiter wanted this!)"
          else
            puts "     ⚠️  Missing '#{missing_skill}' (recruiter wanted this!)"
          end
        end
      end

      if reason_lower.include?("muito junior") || reason_lower.include?("too junior")
        if candidate.position_level&.downcase&.include?("junior") ||
           candidate.role_name&.downcase&.include?("junior")
          puts "     ⚠️  Still Junior (recruiter rejected Junior level!)"
        end
      end

      if reason_lower.include?("pouca experiência") || reason_lower.include?("pouca experiencia")
        puts "     ⚠️  Check experience level (recruiter wanted more experience)"
      end
    end
  end

  def extract_missing_skill(reason)
    patterns = [
      /não sabe (\w+)/,
      /nao sabe (\w+)/,
      /sem (\w+)/,
      /falta (\w+)/,
      /precisa (\w+)/,
      /needs (\w+)/
    ]

    patterns.each do |pattern|
      match = reason.match(pattern)
      return match[1] if match
    end

    nil
  end

  def extract_wanted_skills(disliked_reasons)
    skills = []

    disliked_reasons.each do |reason|
      reason_lower = reason.downcase

      if reason_lower.include?("não sabe") || reason_lower.include?("nao sabe")
        skill = extract_missing_skill(reason_lower)
        skills << skill if skill
      end
    end

    skills.uniq
  end

  def analyze_skill_patterns(candidates, disliked_reasons)
    print_section("📊 SKILL PATTERN ANALYSIS")

    all_skills = []
    candidates.each do |result|
      skills = extract_skills(result[:candidate])
      all_skills.concat(skills)
    end

    skill_frequency = all_skills.tally.sort_by { |_, count| -count }

    puts "\n  🔝 Most common skills in new candidates:"
    skill_frequency.take(15).each do |skill, count|
      percentage = (count.to_f / candidates.count * 100).round(1)
      puts "     • #{skill}: #{count}/#{candidates.count} (#{percentage}%)"

      disliked_reasons.each do |reason|
        reason_lower = reason.downcase
        skill_lower = skill.downcase

        if reason_lower.include?("não sabe #{skill_lower}") ||
            reason_lower.include?("nao sabe #{skill_lower}")
          puts "       🚨 ALERT: This skill was REJECTED in feedback!"
        end
      end
    end

    wanted_skills = extract_wanted_skills(disliked_reasons)

    if wanted_skills.any?
      puts "\n  🎯 SEMANTIC ANALYSIS (based on rejection reasons):"
      puts "     Recruiter WANTS candidates with: #{wanted_skills.join(', ')}"

      wanted_skills.each do |skill|
        count = candidates.count do |result|
          skills = extract_skills(result[:candidate])
          skills.any? { |s| s.downcase.include?(skill) }
        end

        percentage = (count.to_f / candidates.count * 100).round(1)
        puts "\n     #{skill.upcase}: #{count}/#{candidates.count} (#{percentage}%)"

        if count > candidates.count / 2
          puts "     ✅ GOOD: Majority have #{skill} (matching recruiter intent)"
        elsif count > 0
          puts "     ⚠️  PARTIAL: Some candidates have #{skill}"
        else
          puts "     ❌ PROBLEM: NO candidates with #{skill}!"
          puts "     → Vectorial refinement failed to capture semantic intent"
        end
      end

      puts "\n  ⚠️  IMPORTANT NOTE:"
      puts "     Vectorial refinement moves AWAY from rejected candidates' embeddings."
      puts "     It does NOT understand textual reasons like 'não sabe rails'."
      puts "     If rejected candidate is 'Java dev' and reason is 'needs Rails',"
      puts "     the system moves away from 'Java dev' profile, not towards 'Rails'."
    end
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

  def search_with_embedding(embedding, exclude_ids:, threshold:, limit:)
    sql = <<-SQL
      SELECT#{' '}
        e.reference_id as candidate_id,
        1 - (e.embedding <=> $1::vector) as similarity
      FROM embeddings e
      WHERE e.reference_type = 'Candidate'
        AND e.reference_id NOT IN (#{exclude_ids.any? ? exclude_ids.join(',') : 'NULL'})
        AND 1 - (e.embedding <=> $1::vector) >= $2
      ORDER BY similarity DESC
      LIMIT $3
    SQL

    results = ActiveRecord::Base.connection.exec_query(
      sql,
      "SQL",
      [
        "[#{embedding.join(',')}]",
        threshold,
        limit
      ]
    )

    candidate_ids = results.map { |r| r["candidate_id"] }
    candidates = Candidate.where(id: candidate_ids, account_id: @account_id).index_by(&:id)

    results.map do |r|
      {
        candidate: candidates[r["candidate_id"]],
        score: r["similarity"].to_f
      }
    end.compact.select { |r| r[:candidate].present? }
  end

  def cosine_similarity(vec1, vec2)
    dot_product = vec1.zip(vec2).sum { |a, b| a * b }
    mag1 = Math.sqrt(vec1.sum { |v| v**2 })
    mag2 = Math.sqrt(vec2.sum { |v| v**2 })

    return 0.0 if mag1.zero? || mag2.zero?

    dot_product / (mag1 * mag2)
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

puts "🔍 Refinement Quality Analyzer loaded!"
puts ""
puts "Usage:"
puts "  analyzer = RefinementQualityAnalyzer.new(sourcing_id)"
puts "  analyzer.analyze"
puts ""
puts "Example:"
puts "  analyzer = RefinementQualityAnalyzer.new(564)"
puts "  analyzer.analyze"
