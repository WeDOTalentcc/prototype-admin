# frozen_string_literal: true

# Script para testar extração de data_raw
# Usage: rails c
#        load 'scripts/test_data_raw_extraction.rb'
#        test_candidate(candidate_id)

def test_candidate(candidate_id)
  candidate = Candidate.find(candidate_id)

  unless candidate.data_raw.present?
    puts "❌ Candidate #{candidate_id} has no data_raw"
    return
  end

  data = JSON.parse(candidate.data_raw)

  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "🔍 Candidate ##{candidate.id}: #{candidate.name}"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts ""

  # Test experiences
  experiences = data["experiences_a"] || []
  puts "💼 EXPERIENCES (#{experiences.size} found in data_raw)"
  puts ""

  if experiences.any?
    experiences.each_with_index do |exp, idx|
      company = exp["company_name"]&.strip
      occupation = exp["occupation_name"]&.strip
      start_date = exp["start_date"]
      end_date = exp["end_date"]

      valid = company.present? && occupation.present?
      status = valid ? "✅" : "❌"

      puts "#{status} Experience ##{idx + 1}:"
      puts "   Company: #{company || '(blank)'}"
      puts "   Occupation: #{occupation || '(blank)'}"
      puts "   Period: #{start_date} → #{end_date || 'present'}"
      puts "   Valid: #{valid}"
      puts ""
    end

    valid_count = experiences.count { |e| e["company_name"]&.strip.present? && e["occupation_name"]&.strip.present? }
    puts "Summary: #{valid_count}/#{experiences.size} valid experiences"
  else
    puts "No experiences found in data_raw"
  end

  puts ""
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Test educations
  educations = data["educations_a"] || []
  puts "🎓 EDUCATIONS (#{educations.size} found in data_raw)"
  puts ""

  if educations.any?
    educations.each_with_index do |edu, idx|
      institution = edu["institution_name"]&.strip
      study_area = edu["study_area_name"]&.strip
      start_date = edu["start_date"]
      end_date = edu["end_date"]

      valid = institution.present?
      status = valid ? "✅" : "❌"

      puts "#{status} Education ##{idx + 1}:"
      puts "   Institution: #{institution || '(blank)'}"
      puts "   Study Area: #{study_area || '(blank)'}"
      puts "   Period: #{start_date || '?'} → #{end_date || 'present'}"
      puts "   Valid: #{valid}"
      puts ""
    end

    valid_count = educations.count { |e| e["institution_name"]&.strip.present? }
    puts "Summary: #{valid_count}/#{educations.size} valid educations"
  else
    puts "No educations found in data_raw"
  end

  puts ""
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Check current DB state
  puts "📊 DATABASE STATE:"
  puts "   Experiences in DB: #{candidate.experiences.count}"
  puts "   Educations in DB: #{candidate.educations.count}"
  puts ""

  # LinkedIn check
  linkedin_raw = data["linkedin"]
  puts "🔗 LINKEDIN:"
  puts "   In data_raw: #{linkedin_raw || '(none)'}"
  puts "   In DB: #{candidate.linkedin || '(none)'}"
  puts ""

  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

rescue JSON::ParserError => e
  puts "❌ Failed to parse data_raw: #{e.message}"
rescue => e
  puts "❌ Error: #{e.message}"
  puts e.backtrace.first(5)
end

def analyze_all_data_raw(account_id: nil, sample_size: 100)
  scope = Candidate.where.not(data_raw: nil)
  scope = scope.where(account_id: account_id) if account_id

  total = scope.count
  sample = scope.limit(sample_size)

  stats = {
    total_candidates: 0,
    has_experiences_in_raw: 0,
    has_educations_in_raw: 0,
    total_experiences_in_raw: 0,
    total_educations_in_raw: 0,
    valid_experiences: 0,
    valid_educations: 0,
    has_linkedin_in_raw: 0
  }

  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "📊 Analyzing data_raw (sample: #{sample_size} of #{total})"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts ""

  sample.find_each do |candidate|
    stats[:total_candidates] += 1

    begin
      data = JSON.parse(candidate.data_raw)

      # Experiences
      experiences = data["experiences_a"] || []
      if experiences.any?
        stats[:has_experiences_in_raw] += 1
        stats[:total_experiences_in_raw] += experiences.size
        stats[:valid_experiences] += experiences.count { |e|
          e["company_name"]&.strip.present? && e["occupation_name"]&.strip.present?
        }
      end

      # Educations
      educations = data["educations_a"] || []
      if educations.any?
        stats[:has_educations_in_raw] += 1
        stats[:total_educations_in_raw] += educations.size
        stats[:valid_educations] += educations.count { |e|
          e["institution_name"]&.strip.present?
        }
      end

      # LinkedIn
      if data["linkedin"].present?
        stats[:has_linkedin_in_raw] += 1
      end

    rescue => e
      # Skip parse errors
    end
  end

  puts "Results:"
  puts ""
  puts "💼 EXPERIENCES:"
  puts "   Candidates with experiences in raw: #{stats[:has_experiences_in_raw]} (#{(stats[:has_experiences_in_raw].to_f / stats[:total_candidates] * 100).round(2)}%)"
  puts "   Total experiences found: #{stats[:total_experiences_in_raw]}"
  puts "   Valid experiences: #{stats[:valid_experiences]}"
  puts "   Avg per candidate: #{(stats[:total_experiences_in_raw].to_f / [ stats[:has_experiences_in_raw], 1 ].max).round(2)}"
  puts ""
  puts "🎓 EDUCATIONS:"
  puts "   Candidates with educations in raw: #{stats[:has_educations_in_raw]} (#{(stats[:has_educations_in_raw].to_f / stats[:total_candidates] * 100).round(2)}%)"
  puts "   Total educations found: #{stats[:total_educations_in_raw]}"
  puts "   Valid educations: #{stats[:valid_educations]}"
  puts "   Avg per candidate: #{(stats[:total_educations_in_raw].to_f / [ stats[:has_educations_in_raw], 1 ].max).round(2)}"
  puts ""
  puts "🔗 LINKEDIN:"
  puts "   Candidates with linkedin in raw: #{stats[:has_linkedin_in_raw]} (#{(stats[:has_linkedin_in_raw].to_f / stats[:total_candidates] * 100).round(2)}%)"
  puts ""
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Extrapolate to full database
  if sample_size < total
    puts ""
    puts "📈 EXTRAPOLATION (estimated for all #{total} candidates):"
    multiplier = total.to_f / sample_size
    puts "   Total experiences: ~#{(stats[:total_experiences_in_raw] * multiplier).round}"
    puts "   Valid experiences: ~#{(stats[:valid_experiences] * multiplier).round}"
    puts "   Total educations: ~#{(stats[:total_educations_in_raw] * multiplier).round}"
    puts "   Valid educations: ~#{(stats[:valid_educations] * multiplier).round}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end
end

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "Data Raw Extraction Test Script Loaded"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""
puts "Usage:"
puts "  # Test single candidate"
puts "  test_candidate(435748)"
puts ""
puts "  # Analyze sample of data_raw"
puts "  analyze_all_data_raw(account_id: 2, sample_size: 100)"
puts ""
puts "  # Analyze larger sample"
puts "  analyze_all_data_raw(account_id: 2, sample_size: 1000)"
puts ""
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
