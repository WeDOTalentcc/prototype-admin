# frozen_string_literal: true

module DiagnoseCandidateData
  class << self
    def investigate(account_id: nil)
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "🔍 Investigating Candidate Data Sources"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      scope = account_id ? Candidate.where(account_id: account_id) : Candidate

      total = scope.count
      with_data_raw = scope.where.not(data_raw: nil).count
      without_data_raw = scope.where(data_raw: nil).count

      puts "\n📊 DATA_RAW STATUS:"
      puts "   Total candidates: #{total}"
      puts "   With data_raw: #{with_data_raw} (#{percentage(with_data_raw, total)}%)"
      puts "   Without data_raw (NULL): #{without_data_raw} (#{percentage(without_data_raw, total)}%)"

      # Check experiences/educations
      total_exp = Experience.count
      total_edu = Education.count
      candidates_with_exp = Candidate.joins(:experiences).distinct.count
      candidates_with_edu = Candidate.joins(:educations).distinct.count

      puts "\n💼 EXPERIENCES IN DATABASE:"
      puts "   Total Experience records: #{total_exp}"
      puts "   Candidates with experiences: #{candidates_with_exp}"
      puts "   Avg per candidate: #{total_exp.to_f / candidates_with_exp rescue 0}"

      puts "\n🎓 EDUCATIONS IN DATABASE:"
      puts "   Total Education records: #{total_edu}"
      puts "   Candidates with educations: #{candidates_with_edu}"
      puts "   Avg per candidate: #{total_edu.to_f / candidates_with_edu rescue 0}"

      # Sample candidates WITH data_raw
      puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "📋 SAMPLE: Candidates WITH data_raw"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      samples_with = scope.where.not(data_raw: nil).limit(5)
      if samples_with.any?
        samples_with.each do |c|
          analyze_candidate_data(c)
        end
      else
        puts "   ❌ No candidates with data_raw found!"
      end

      # Sample candidates WITHOUT data_raw but WITH experiences
      puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "📋 SAMPLE: Candidates WITHOUT data_raw but WITH experiences"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      samples_exp = scope.where(data_raw: nil).joins(:experiences).limit(5)
      if samples_exp.any?
        samples_exp.each do |c|
          puts "\n   Candidate ##{c.id} - #{c.name}"
          puts "   Source: #{c.source}"
          puts "   Has data_raw: NO"
          puts "   Experiences: #{c.experiences.count}"
          puts "   Educations: #{c.educations.count}"

          if c.experiences.any?
            exp = c.experiences.first
            puts "   Sample experience:"
            puts "      Company: #{exp.company&.name}"
            puts "      Occupation: #{exp.occupation&.name}"
            puts "      Dates: #{exp.start_date} → #{exp.end_date}"
          end
        end
      else
        puts "   ℹ️  No candidates found with this criteria"
      end

      puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "🎯 RECOMMENDATION:"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      if with_data_raw == 0
        puts "   ⚠️  NO data_raw found! Data may have been:"
        puts "      1. Already migrated previously"
        puts "      2. Imported directly to Experience/Education models"
        puts "      3. Never stored in data_raw field"
        puts "\n   ✅ Experiences/Educations already exist in database!"
        puts "      → No migration needed from data_raw"
      elsif with_data_raw < total * 0.1
        puts "   ⚠️  Very few candidates have data_raw (#{percentage(with_data_raw, total)}%)"
        puts "      → Majority already migrated or imported elsewhere"
      else
        puts "   ✅ Ready to migrate #{with_data_raw} candidates from data_raw"
      end

      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def analyze_candidate_data(candidate)
      puts "\n   Candidate ##{candidate.id} - #{candidate.name}"
      puts "   Source: #{candidate.source}"

      return unless candidate.data_raw

      begin
        data = JSON.parse(candidate.data_raw)

        experiences = data["experiences_a"] || data["experiences"] || []
        educations = data["educations_a"] || data["educations"] || []
        linkedin = data["linkedin"]

        puts "   data_raw keys: #{data.keys.join(', ')}"
        puts "   Experiences in data_raw: #{experiences.size}"
        puts "   Educations in data_raw: #{educations.size}"
        puts "   LinkedIn in data_raw: #{linkedin.present? ? 'YES' : 'NO'}"
        puts "   Already has Experience records: #{candidate.experiences.count}"
        puts "   Already has Education records: #{candidate.educations.count}"

        if experiences.any?
          exp = experiences.first
          puts "   Sample experience from data_raw:"
          puts "      Company: #{exp['company_name']}"
          puts "      Occupation: #{exp['occupation_name']}"
        end
      rescue => e
        puts "   ❌ Error parsing data_raw: #{e.message}"
        puts "   data_raw preview: #{candidate.data_raw[0..200]}"
      end
    end

    def check_orphaned_experiences
      puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "🔍 Checking for orphaned Experience/Education records"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      orphaned_exp = Experience.where.not(candidate_id: Candidate.select(:id)).count
      orphaned_edu = Education.where.not(candidate_id: Candidate.select(:id)).count

      puts "   Orphaned Experiences (no candidate): #{orphaned_exp}"
      puts "   Orphaned Educations (no candidate): #{orphaned_edu}"

      if orphaned_exp > 0 || orphaned_edu > 0
        puts "\n   ⚠️  Found orphaned records! These should be cleaned up."
      end

      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def find_candidates_with_data_raw(account_id: nil, limit: 20)
      scope = account_id ? Candidate.where(account_id: account_id) : Candidate
      candidates = scope.where.not(data_raw: nil).limit(limit)

      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "📋 Candidates with data_raw (limit: #{limit})"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      if candidates.empty?
        puts "   ❌ No candidates with data_raw found!"
        return []
      end

      candidates.each do |c|
        data = JSON.parse(c.data_raw) rescue {}
        exp_count = (data["experiences_a"] || []).size
        edu_count = (data["educations_a"] || []).size

        puts "   ID: #{c.id} | Account: #{c.account_id} | Exp: #{exp_count} | Edu: #{edu_count} | Source: #{c.source}"
      end

      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      candidates.pluck(:id)
    end

    private

    def percentage(part, total)
      return 0 if total == 0
      ((part.to_f / total) * 100).round(2)
    end
  end
end

# Helper methods for console
def investigate_data(account_id: nil)
  DiagnoseCandidateData.investigate(account_id: account_id)
end

def check_orphaned_records
  DiagnoseCandidateData.check_orphaned_experiences
end

def find_data_raw_candidates(account_id: nil, limit: 20)
  DiagnoseCandidateData.find_candidates_with_data_raw(account_id: account_id, limit: limit)
end

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "🔍 Candidate Data Diagnostic Script Loaded"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""
puts "Usage:"
puts "  # Full investigation"
puts "  investigate_data(account_id: 1)"
puts "  investigate_data(account_id: 2)"
puts "  investigate_data  # All accounts"
puts ""
puts "  # Check orphaned records"
puts "  check_orphaned_records"
puts ""
puts "  # Find candidates WITH data_raw"
puts "  find_data_raw_candidates(account_id: 1)"
puts "  find_data_raw_candidates(account_id: 2)"
puts ""
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
