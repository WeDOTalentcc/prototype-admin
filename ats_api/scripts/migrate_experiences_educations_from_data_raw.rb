# frozen_string_literal: true

# Script to migrate Experiences and Educations from data_raw
# Usage: rails c
#        load 'scripts/migrate_experiences_educations_from_data_raw.rb'

module MigrateExperiencesEducationsFromDataRaw
  class << self
    def execute(account_id: nil, dry_run: true, migrate_type: :both)
      scope = build_scope(account_id, migrate_type)

      total_count = scope.count

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 Starting #{migrate_type.to_s.upcase} migration from data_raw"
      Rails.logger.info "   Dry run: #{dry_run}"
      Rails.logger.info "   Account filter: #{account_id || 'ALL'}"
      Rails.logger.info "   Total candidates to process: #{total_count}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      stats = {
        total: 0,
        experiences_created: 0,
        educations_created: 0,
        experiences_found_in_raw: 0,
        educations_found_in_raw: 0,
        experiences_attempted: 0,
        educations_attempted: 0,
        errors: 0,
        skipped: 0
      }

      start_time = Time.current
      last_log_time = start_time

      scope.find_each do |candidate|
        stats[:total] += 1

        begin
          result = process_candidate(candidate, dry_run: dry_run, migrate_type: migrate_type)

          stats[:experiences_created] += result[:experiences_created]
          stats[:educations_created] += result[:educations_created]
          stats[:experiences_found_in_raw] += result[:experiences_found]
          stats[:educations_found_in_raw] += result[:educations_found]
          stats[:experiences_attempted] += result[:experiences_attempted]
          stats[:educations_attempted] += result[:educations_attempted]
          stats[:skipped] += 1 if result[:skipped]

          # Log progress every 50 records or every 10 seconds
          current_time = Time.current
          should_log = (stats[:total] % 50 == 0) || (current_time - last_log_time > 10)

          if should_log
            last_log_time = current_time
            elapsed = current_time - start_time
            percentage = (stats[:total].to_f / total_count * 100).round(2)
            remaining = total_count - stats[:total]
            rate = stats[:total] / elapsed
            eta_seconds = remaining / rate
            eta = format_duration(eta_seconds)

            Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            Rails.logger.info "📊 Progress: #{percentage}% (#{stats[:total]}/#{total_count})"
            Rails.logger.info "   💼 Experiences - Found: #{stats[:experiences_found_in_raw]} | Attempted: #{stats[:experiences_attempted]} | Created: #{stats[:experiences_created]}"
            Rails.logger.info "   🎓 Educations - Found: #{stats[:educations_found_in_raw]} | Attempted: #{stats[:educations_attempted]} | Created: #{stats[:educations_created]}"
            Rails.logger.info "   ⏭️  Skipped: #{stats[:skipped]}"
            Rails.logger.info "   ❌ Errors: #{stats[:errors]}"
            Rails.logger.info "   ⏱️  Elapsed: #{format_duration(elapsed)}"
            Rails.logger.info "   ⏳ ETA: #{eta} (#{remaining} remaining)"
            Rails.logger.info "   🚀 Rate: #{rate.round(2)} records/sec"
            Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          end
        rescue => e
          stats[:errors] += 1
          Rails.logger.error "❌ Error processing candidate #{candidate.id}: #{e.message}"
          Rails.logger.error e.backtrace.first(3).join("\n")
        end
      end

      stats[:elapsed_time] = Time.current - start_time

      print_summary(stats, dry_run, migrate_type)
      stats
    end

    private

    def build_scope(account_id, migrate_type)
      # Query otimizada usando LEFT JOIN para encontrar candidatos sem experiences/educations
      scope = Candidate.where.not(data_raw: nil)

      case migrate_type
      when :experiences
        scope = scope.left_joins(:experiences).where(experiences: { id: nil })
      when :educations
        scope = scope.left_joins(:educations).where(educations: { id: nil })
      when :both
        scope = scope.left_joins(:experiences, :educations)
                     .where("experiences.id IS NULL OR educations.id IS NULL")
      end

      scope = scope.where(account_id: account_id) if account_id
      scope.distinct
    end

    def process_candidate(candidate, dry_run:, migrate_type:)
      data = parse_data_raw(candidate.data_raw)

      return {
        experiences_created: 0,
        educations_created: 0,
        experiences_found: 0,
        educations_found: 0,
        experiences_attempted: 0,
        educations_attempted: 0,
        skipped: true
      } unless data

      result = {
        experiences_created: 0,
        educations_created: 0,
        experiences_found: 0,
        educations_found: 0,
        experiences_attempted: 0,
        educations_attempted: 0,
        skipped: false
      }

      # Migrate experiences
      if [ :experiences, :both ].include?(migrate_type) && candidate.experiences.empty?
        exp_result = migrate_experiences(candidate, data, dry_run)
        result[:experiences_created] = exp_result[:created]
        result[:experiences_found] = exp_result[:found]
        result[:experiences_attempted] = exp_result[:attempted]
      end

      # Migrate educations
      if [ :educations, :both ].include?(migrate_type) && candidate.educations.empty?
        edu_result = migrate_educations(candidate, data, dry_run)
        result[:educations_created] = edu_result[:created]
        result[:educations_found] = edu_result[:found]
        result[:educations_attempted] = edu_result[:attempted]
      end

      result
    end

    def migrate_experiences(candidate, data, dry_run)
      experiences_data = extract_experiences(data)
      found_count = experiences_data&.size || 0

      return { found: found_count, attempted: 0, created: 0 } if experiences_data.blank?

      attempted = 0
      created = 0

      experiences_data.each do |exp_data|
        next if exp_data.blank?

        company_name = exp_data["company_name"]&.strip
        occupation_name = exp_data["occupation_name"]&.strip
        has_start_date = exp_data["start_date"].present?
        has_end_date = exp_data["end_date"].present?
        has_description = exp_data["description"].present?

        # Skip only if there's NO useful data at all
        has_any_useful_data = company_name.present? || occupation_name.present? ||
                              has_start_date || has_end_date || has_description

        unless has_any_useful_data
          Rails.logger.debug "   ⚠️  Skipping empty experience entry"
          next
        end

        attempted += 1

        unless dry_run
          begin
            # Use placeholder if company/occupation name is blank
            company = if company_name.present?
                        find_or_create_company(company_name, candidate.account_id)
            else
                        find_or_create_company("[unknown company]", candidate.account_id)
            end

            occupation = if occupation_name.present?
                           find_or_create_occupation(occupation_name, candidate.account_id)
            else
                           find_or_create_occupation("[unknown occupation]", candidate.account_id)
            end

            start_date = parse_date(exp_data["start_date"])
            end_date = parse_date(exp_data["end_date"])

            Experience.create!(
              candidate_id: candidate.id,
              account_id: candidate.account_id,
              company_id: company.id,
              occupation_id: occupation.id,
              start_date: start_date,
              end_date: end_date,
              work_here: exp_data["end_date"].blank?,
              description: exp_data["description"],
              parse_language: exp_data["parse_language"]
            )
            created += 1
          rescue => e
            Rails.logger.error "   ❌ Failed to create experience: #{e.message}"
          end
        else
          created += 1 # Count as created in dry run
        end
      end

      { found: found_count, attempted: attempted, created: created }
    rescue => e
      Rails.logger.error "Error migrating experiences for candidate #{candidate.id}: #{e.message}"
      { found: found_count, attempted: 0, created: 0 }
    end

    def migrate_educations(candidate, data, dry_run)
      educations_data = extract_educations(data)
      found_count = educations_data&.size || 0

      return { found: found_count, attempted: 0, created: 0 } if educations_data.blank?

      attempted = 0
      created = 0

      educations_data.each do |edu_data|
        next if edu_data.blank?

        institution_name = edu_data["institution_name"]&.strip
        study_area_name = edu_data["study_area_name"]&.strip

        if institution_name.blank?
          Rails.logger.debug "   ⚠️  Skipping education: institution='#{institution_name}'"
          next
        end

        attempted += 1

        unless dry_run
          begin
            institution = find_or_create_institution(institution_name, candidate.account_id)
            study_area = find_or_create_study_area(study_area_name, candidate.account_id) if study_area_name.present?

            Education.create!(
              candidate_id: candidate.id,
              account_id: candidate.account_id,
              institution_id: institution.id,
              study_area_id: study_area&.id,
              start_date: parse_date(edu_data["start_date"]),
              end_date: parse_date(edu_data["end_date"]),
              study_here: edu_data["end_date"].blank?,
              formation_type: map_formation_type(edu_data["formation_type"]),
              parse_language: edu_data["parse_language"]
            )
            created += 1
          rescue => e
            Rails.logger.error "   ❌ Failed to create education: #{e.message}"
          end
        else
          created += 1 # Count as created in dry run
        end
      end

      { found: found_count, attempted: attempted, created: created }
    rescue => e
      Rails.logger.error "Error migrating educations for candidate #{candidate.id}: #{e.message}"
      { found: found_count, attempted: 0, created: 0 }
    end

    def parse_data_raw(data_raw)
      return nil if data_raw.blank?

      JSON.parse(data_raw)
    rescue JSON::ParserError => e
      Rails.logger.error "Failed to parse data_raw: #{e.message}"
      nil
    end

    def extract_experiences(data)
      data["experiences_a"] || data[:experiences_a] || []
    end

    def extract_educations(data)
      data["educations_a"] || data[:educations_a] || []
    end

    def parse_date(date_string)
      return nil if date_string.blank?

      DateTime.parse(date_string)
    rescue ArgumentError
      nil
    end

    def find_or_create_company(name, account_id)
      Company.find_or_create_by!(name: name.downcase) do |company|
        company.account_id = account_id
      end
    end

    def find_or_create_occupation(name, account_id)
      Occupation.find_or_create_by!(name: name.downcase) do |occupation|
        occupation.account_id = account_id
      end
    end

    def find_or_create_institution(name, account_id)
      Institution.find_or_create_by!(name: name) do |institution|
        institution.account_id = account_id
        institution.approved = false
      end
    end

    def find_or_create_study_area(name, account_id)
      return nil if name.blank?

      StudyArea.find_or_create_by!(name: name) do |area|
        area.account_id = account_id
      end
    end

    def map_formation_type(type_string)
      # Map string to formation_type enum (default: 8)
      # You may need to adjust this based on your enum values
      return 8 if type_string.blank?

      case type_string.to_s.downcase
      when "mestrado", "master" then 2
      when "bacharelado", "bachelor" then 3
      when "técnico", "technical" then 5
      else 8
      end
    end

    def format_duration(seconds)
      return "0s" if seconds < 1

      hours = (seconds / 3600).to_i
      minutes = ((seconds % 3600) / 60).to_i
      secs = (seconds % 60).to_i

      parts = []
      parts << "#{hours}h" if hours > 0
      parts << "#{minutes}m" if minutes > 0 || hours > 0
      parts << "#{secs}s"

      parts.join(" ")
    end

    def print_summary(stats, dry_run, migrate_type)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ #{migrate_type.to_s.upcase} Migration #{dry_run ? '(DRY RUN)' : 'COMPLETED'}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "📊 Total candidates processed: #{stats[:total]}"
      Rails.logger.info ""
      Rails.logger.info "💼 EXPERIENCES:"
      Rails.logger.info "   Found in data_raw: #{stats[:experiences_found_in_raw]}"
      Rails.logger.info "   Attempted to create: #{stats[:experiences_attempted]}"
      Rails.logger.info "   Successfully created: #{stats[:experiences_created]}"
      if stats[:experiences_attempted] > 0
        success_rate = (stats[:experiences_created].to_f / stats[:experiences_attempted] * 100).round(2)
        Rails.logger.info "   Success rate: #{success_rate}%"
      end
      Rails.logger.info ""
      Rails.logger.info "🎓 EDUCATIONS:"
      Rails.logger.info "   Found in data_raw: #{stats[:educations_found_in_raw]}"
      Rails.logger.info "   Attempted to create: #{stats[:educations_attempted]}"
      Rails.logger.info "   Successfully created: #{stats[:educations_created]}"
      if stats[:educations_attempted] > 0
        success_rate = (stats[:educations_created].to_f / stats[:educations_attempted] * 100).round(2)
        Rails.logger.info "   Success rate: #{success_rate}%"
      end
      Rails.logger.info ""
      Rails.logger.info "   ⏭️  Candidates skipped: #{stats[:skipped]}"
      Rails.logger.info "   ❌ Errors: #{stats[:errors]}"
      Rails.logger.info "   ⏱️  Total time: #{format_duration(stats[:elapsed_time])}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      if dry_run
        Rails.logger.info "💡 This was a DRY RUN. Run with dry_run: false to apply changes"
      end
    end
  end
end

# Helper methods for console usage
def migrate_experiences_educations(account_id: nil, dry_run: true, type: :both)
  MigrateExperiencesEducationsFromDataRaw.execute(
    account_id: account_id,
    dry_run: dry_run,
    migrate_type: type
  )
end

def migrate_experiences_educations!(account_id: nil, type: :both)
  MigrateExperiencesEducationsFromDataRaw.execute(
    account_id: account_id,
    dry_run: false,
    migrate_type: type
  )
end

# Show usage
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "Experiences & Educations Migration Script Loaded"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""
puts "Usage:"
puts "  # Dry run (no changes) - migrate both"
puts "  migrate_experiences_educations(account_id: 2)"
puts ""
puts "  # Dry run - only experiences"
puts "  migrate_experiences_educations(account_id: 2, type: :experiences)"
puts ""
puts "  # Dry run - only educations"
puts "  migrate_experiences_educations(account_id: 2, type: :educations)"
puts ""
puts "  # Actually update - both"
puts "  migrate_experiences_educations!(account_id: 2)"
puts ""
puts "  # Actually update - only experiences"
puts "  migrate_experiences_educations!(account_id: 2, type: :experiences)"
puts ""
puts "  # Test with single candidate"
puts "  candidate = Candidate.find(1179)"
puts "  data = JSON.parse(candidate.data_raw)"
puts "  puts data['experiences_a']"
puts "  puts data['educations_a']"
puts ""
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
