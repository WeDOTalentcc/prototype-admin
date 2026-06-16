# frozen_string_literal: true

def find_candidate_with_sourced_profile(account_id: 1, limit: 10)
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "🔍 Finding candidates with sourced_profile and experiences"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Buscar candidatos com sourced_profile e experiences
  candidates = Candidate
    .where(account_id: account_id)
    .joins("INNER JOIN sourced_profiles ON sourced_profiles.candidate_id = candidates.id")
    .joins(:experiences)
    .distinct
    .limit(limit)

  if candidates.empty?
    puts "   ❌ No candidates found with sourced_profile and experiences"
    return nil
  end

  puts "\n📋 Found #{candidates.count} candidates:\n"

  candidates.each do |c|
    sp = c.sourced_profile.first
    next unless sp

    exp_count = c.experiences.count
    edu_count = c.educations.count

    # Check if has sourcing
    sourcings = SourcedProfileSourcing.where(sourced_profile_id: sp.id)
    sourcing = sourcings.first

    puts "   ID: #{c.id}"
    puts "   Name: #{c.name}"
    puts "   Email: #{c.email}"
    puts "   LinkedIn: #{c.linkedin}"
    puts "   Experiences: #{exp_count}"
    puts "   Educations: #{edu_count}"
    puts "   SourcedProfile ID: #{sp.id}"
    puts "   SourcedProfile Sourcing: #{sourcing ? "YES (ID: #{sourcing.id})" : "NO"}"
    puts "   " + "─" * 60
  end

  # Return first candidate ID
  first_id = candidates.first.id

  puts "\n✅ To inspect first candidate, run:"
  puts "   inspect_candidate(#{first_id})"

  first_id
end

def inspect_candidate(id)
  candidate = Candidate.find(id)

  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "👤 CANDIDATE ##{candidate.id} - #{candidate.name}"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  puts "\n📧 BASIC INFO:"
  puts "   Email: #{candidate.email}"
  puts "   LinkedIn: #{candidate.linkedin}"
  puts "   Source: #{candidate.source}"
  puts "   Current Company: #{candidate.current_company}"
  puts "   Role: #{candidate.role_name}"

  # SourcedProfile
  sourced_profiles = candidate.sourced_profile
  if sourced_profiles.any?
    sp = sourced_profiles.first
    puts "\n🔗 SOURCED PROFILE:"
    puts "   ID: #{sp.id}"
    puts "   Platform: #{sp.platform}"
    puts "   URL: #{sp.url}"
    puts "   Created at: #{sp.created_at}"

    # SourcedProfileSourcing
    sourcings = SourcedProfileSourcing.where(sourced_profile_id: sp.id)
    if sourcings.any?
      puts "\n📊 SOURCED PROFILE SOURCINGS (#{sourcings.count}):"
      sourcings.limit(3).each do |sps|
        puts "      ID: #{sps.id} | Sourcing ID: #{sps.sourcing_id} | Created: #{sps.created_at}"
      end
    else
      puts "\n   ⚠️  No SourcedProfileSourcings found"
    end
  else
    puts "\n   ❌ No SourcedProfile found"
  end

  # Experiences
  experiences = candidate.experiences.order(start_date: :desc)
  puts "\n💼 EXPERIENCES (#{experiences.count}):"

  if experiences.any?
    experiences.limit(5).each_with_index do |exp, i|
      puts "\n   #{i + 1}. #{exp.occupation&.name || 'N/A'} at #{exp.company&.name || 'N/A'}"
      puts "      Period: #{exp.start_date&.strftime('%Y-%m') || 'N/A'} → #{exp.end_date&.strftime('%Y-%m') || 'Current'}"
      puts "      Work here: #{exp.work_here}"
      puts "      Description: #{exp.description&.truncate(100) || 'N/A'}"
    end

    if experiences.count > 5
      puts "\n   ... and #{experiences.count - 5} more experiences"
    end
  else
    puts "   ❌ No experiences found"
  end

  # Educations
  educations = candidate.educations.order(start_date: :desc)
  puts "\n🎓 EDUCATIONS (#{educations.count}):"

  if educations.any?
    educations.limit(3).each_with_index do |edu, i|
      puts "\n   #{i + 1}. #{edu.study_area&.name || 'N/A'} at #{edu.institution&.name || 'N/A'}"
      puts "      Period: #{edu.start_date&.strftime('%Y-%m') || 'N/A'} → #{edu.end_date&.strftime('%Y-%m') || 'Current'}"
      puts "      Type: #{edu.formation_type}"
    end

    if educations.count > 3
      puts "\n   ... and #{educations.count - 3} more educations"
    end
  else
    puts "   ❌ No educations found"
  end

  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  candidate
end

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "✅ Sourced Profile Finder Script Loaded"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""
puts "Usage:"
puts "  # Find candidates with sourced_profile and experiences"
puts "  find_candidate_with_sourced_profile(account_id: 1)"
puts "  find_candidate_with_sourced_profile(account_id: 2)"
puts ""
puts "  # Inspect specific candidate"
puts "  inspect_candidate(1584)"
puts ""
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
