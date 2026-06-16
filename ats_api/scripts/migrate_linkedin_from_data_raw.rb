# frozen_string_literal: true

# Script to migrate LinkedIn URLs from data_raw to linkedin field
# Also updates sourced_profile records
# Usage: rails c
#        load 'scripts/migrate_linkedin_from_data_raw.rb'

module MigrateLinkedinFromDataRaw
  class << self
    def execute(account_id: nil, dry_run: true)
      # Optimize query to use index
      scope = build_scope(account_id)

      total_count = scope.count

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 Starting LinkedIn migration from data_raw"
      Rails.logger.info "   Dry run: #{dry_run}"
      Rails.logger.info "   Account filter: #{account_id || 'ALL'}"
      Rails.logger.info "   Total candidates to process: #{total_count}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      stats = {
        total: 0,
        updated: 0,
        sourced_profile_updated: 0,
        errors: 0,
        skipped: 0
      }

      start_time = Time.current
      last_log_time = start_time

      scope.find_each do |candidate|
        stats[:total] += 1

        begin
          result = process_candidate(candidate, dry_run: dry_run)

          case result[:status]
          when :updated
            stats[:updated] += 1
            stats[:sourced_profile_updated] += 1 if result[:sourced_profile_updated]
          when :skipped
            stats[:skipped] += 1
          end

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
            Rails.logger.info "   ✅ Updated: #{stats[:updated]}"
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
        end
      end

      stats[:elapsed_time] = Time.current - start_time

      print_summary(stats, dry_run)
      stats
    end

    private

    def build_scope(account_id)
      # Query otimizada para usar índices parciais:
      # - index_candidates_on_account_id_where_data_raw_present
      # - index_candidates_on_account_id_where_linkedin_null
      scope = Candidate.where.not(data_raw: nil).where(linkedin: nil)
      scope = scope.where(account_id: account_id) if account_id
      scope
    end

    def process_candidate(candidate, dry_run:)
      data = parse_data_raw(candidate.data_raw)
      return { status: :skipped, reason: "No data_raw parsed" } unless data

      linkedin_from_raw = extract_linkedin(data)
      return { status: :skipped, reason: "No linkedin in data_raw" } unless linkedin_from_raw

      normalized_linkedin = normalize_linkedin_url(linkedin_from_raw)
      return { status: :skipped, reason: "Invalid linkedin URL" } unless normalized_linkedin

      current_linkedin = candidate.linkedin
      sourced_profile_updated = false

      if current_linkedin.blank?
        Rails.logger.info "🔍 Candidate ##{candidate.id} (#{candidate.name})"
        Rails.logger.info "   Current: #{current_linkedin.inspect}"
        Rails.logger.info "   From data_raw: #{normalized_linkedin}"

        unless dry_run
          candidate.update!(linkedin: normalized_linkedin)
          Rails.logger.info "   ✅ Updated candidate linkedin"
        end
      elsif normalize_linkedin_url(current_linkedin) != normalized_linkedin
        Rails.logger.warn "⚠️  Candidate ##{candidate.id}: LinkedIn mismatch"
        Rails.logger.warn "   Current: #{current_linkedin}"
        Rails.logger.warn "   From data_raw: #{normalized_linkedin}"
        return { status: :skipped, reason: "LinkedIn mismatch" }
      else
        return { status: :skipped, reason: "LinkedIn already set correctly" }
      end

      # Update sourced_profile if exists
      if candidate.respond_to?(:sourced_profile) && candidate.sourced_profile.present?
        sourced_profile = candidate.sourced_profile

        if sourced_profile.linkedin.blank?
          Rails.logger.info "   📝 Updating sourced_profile linkedin"

          unless dry_run
            sourced_profile.update!(linkedin: normalized_linkedin)
            sourced_profile_updated = true
            Rails.logger.info "   ✅ Updated sourced_profile"
          end
        end
      end

      {
        status: :updated,
        sourced_profile_updated: sourced_profile_updated,
        linkedin: normalized_linkedin
      }
    end

    def parse_data_raw(data_raw)
      return nil if data_raw.blank?

      JSON.parse(data_raw)
    rescue JSON::ParserError => e
      Rails.logger.error "Failed to parse data_raw: #{e.message}"
      nil
    end

    def extract_linkedin(data)
      linkedin = data["linkedin"] || data[:linkedin]
      return nil if linkedin.blank?

      linkedin.to_s.strip
    end

    def normalize_linkedin_url(url)
      return nil if url.blank?

      url = url.strip.downcase

      # Remove trailing slashes
      url = url.gsub(/\/+$/, '')

      # If it doesn't start with http, add https://www.
      unless url.start_with?('http')
        url = "https://www.#{url}" unless url.start_with?('www.')
        url = "https://#{url}" if url.start_with?('www.')
      end

      # Ensure it's a valid LinkedIn URL
      return nil unless url.match?(/linkedin\.com\/in\//)

      # Extract just the profile part
      if url =~ /linkedin\.com\/in\/([^\/\?]+)/
        username = Regexp.last_match(1)
        return "https://www.linkedin.com/in/#{username}"
      end

      url
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

    def print_summary(stats, dry_run)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ LinkedIn Migration #{dry_run ? '(DRY RUN)' : 'COMPLETED'}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "📊 Total candidates processed: #{stats[:total]}"
      Rails.logger.info "   ✅ Updated: #{stats[:updated]} (#{percentage_of(stats[:updated], stats[:total])}%)"
      Rails.logger.info "   📝 Sourced profiles updated: #{stats[:sourced_profile_updated]}"
      Rails.logger.info "   ⏭️  Skipped: #{stats[:skipped]} (#{percentage_of(stats[:skipped], stats[:total])}%)"
      Rails.logger.info "   ❌ Errors: #{stats[:errors]}"
      Rails.logger.info "   ⏱️  Total time: #{format_duration(stats[:elapsed_time])}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      if dry_run
        Rails.logger.info "💡 This was a DRY RUN. Run with dry_run: false to apply changes"
      end
    end

    def percentage_of(part, total)
      return 0 if total.zero?
      ((part.to_f / total) * 100).round(2)
    end
  end
end

# Helper methods for console usage
def migrate_linkedin(account_id: nil, dry_run: true)
  MigrateLinkedinFromDataRaw.execute(account_id: account_id, dry_run: dry_run)
end

def migrate_linkedin!(account_id: nil)
  MigrateLinkedinFromDataRaw.execute(account_id: account_id, dry_run: false)
end

# Show usage
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "LinkedIn Migration Script Loaded"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""
puts "Usage:"
puts "  # Dry run (no changes) for all accounts"
puts "  migrate_linkedin"
puts ""
puts "  # Dry run for specific account"
puts "  migrate_linkedin(account_id: 2)"
puts ""
puts "  # Actually update (all accounts)"
puts "  migrate_linkedin!"
puts ""
puts "  # Actually update (specific account)"
puts "  migrate_linkedin!(account_id: 2)"
puts ""
puts "  # Test with single candidate"
puts "  candidate = Candidate.find(1179)"
puts "  data = JSON.parse(candidate.data_raw)"
puts "  linkedin = data['linkedin']"
puts "  puts linkedin"
puts ""
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
