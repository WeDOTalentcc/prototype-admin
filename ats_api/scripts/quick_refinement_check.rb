# frozen_string_literal: true

sourcing_id = 564

puts "━" * 80
puts "🔍 QUICK REFINEMENT CHECK - Sourcing ##{sourcing_id}"
puts "━" * 80

sourcing = Sourcing.find(sourcing_id)
feedbacks = CandidateFeedback.where(sourcing_id: sourcing_id)

likes = feedbacks.where(feedback_type: "like")
dislikes = feedbacks.where(feedback_type: "dislike")

puts "\n📊 FEEDBACKS:"
puts "  ✅ Likes: #{likes.count}"
puts "  ❌ Dislikes: #{dislikes.count}"

if dislikes.any?
  puts "\n❌ REJECTION REASONS:"
  dislikes.each do |fb|
    puts "  • #{fb.candidate.name}: \"#{fb.reason}\""
  end
end

if likes.any?
  puts "\n✅ LIKED CANDIDATES:"
  likes.each do |fb|
    candidate = fb.candidate
    puts "  • #{candidate.name} - #{candidate.role_name}"
  end
end

base_ids = sourcing.parameters["base_candidate_ids"]
original_vectors = Embedding.where(reference_type: "Candidate", reference_id: base_ids).pluck(:embedding)

if original_vectors.empty?
  puts "\n❌ No embeddings found for base candidates!"
  exit
end

dims = original_vectors.first.size
original_centroid = Array.new(dims, 0.0)
original_vectors.each { |vec| vec.each_with_index { |v, i| original_centroid[i] += v } }
original_centroid.map! { |v| v / original_vectors.size }

service = Candidates::SimilarCandidates::EmbeddingRefinementService.new(
  original_centroid: original_centroid
)

refined_centroid = service.refine(
  liked_ids: likes.pluck(:candidate_id),
  disliked_ids: dislikes.pluck(:candidate_id)
)

puts "\n🔄 REFINEMENT APPLIED"
puts "  Vector dimensions: #{dims}"
puts "  Alpha (like weight): 0.3"
puts "  Beta (dislike weight): 0.2"

existing_ids = SourcedProfileSourcing
  .joins(:sourced_profile)
  .where(sourcing_id: sourcing_id)
  .pluck("sourced_profiles.candidate_id")

exclude_ids = (existing_ids + dislikes.pluck(:candidate_id)).uniq

puts "\n🔍 SEARCHING WITH REFINED VECTOR..."
puts "  Excluding: #{exclude_ids.count} candidates"

sql = <<-SQL
  SELECT#{' '}
    e.reference_id as candidate_id,
    1 - (e.embedding <=> $1::vector) as similarity
  FROM embeddings e
  WHERE e.reference_type = 'Candidate'
    AND e.reference_id NOT IN (#{exclude_ids.any? ? exclude_ids.join(',') : 'NULL'})
    AND 1 - (e.embedding <=> $1::vector) >= 0.60
  ORDER BY similarity DESC
  LIMIT 10
SQL

results = ActiveRecord::Base.connection.exec_query(
  sql,
  "SQL",
  [ "[#{refined_centroid.join(',')}]", 0.60, 10 ]
)

puts "\n📋 TOP 10 NEW CANDIDATES:"
results.each_with_index do |r, idx|
  candidate = Candidate.find(r["candidate_id"])
  score = (r["similarity"].to_f * 100).round(1)

  puts "\n#{idx + 1}. #{candidate.name} (#{score}%)"
  puts "   #{candidate.role_name} @ #{candidate.current_company}"

  text = candidate.curriculum_text&.downcase || ""
  checks = []

  dislikes.each do |fb|
    reason = fb.reason.downcase

    if reason.include?("não sabe rails") || reason.include?("nao sabe rails")
      if text.include?("rails")
        checks << "⚠️  Has Rails (but feedback rejected Rails!)"
      else
        checks << "✅ No Rails"
      end
    end

    if reason.include?("junior")
      if candidate.role_name&.downcase&.include?("junior")
        checks << "⚠️  Junior level (but feedback rejected Junior!)"
      end
    end
  end

  checks.each { |check| puts "   #{check}" }
end

puts "\n" + "━" * 80
puts "✅ Analysis complete!"
puts "━" * 80
