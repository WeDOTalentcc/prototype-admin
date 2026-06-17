#!/usr/bin/env ruby

require_relative "../config/environment"

Rails.logger = Logger.new($stdout)
Rails.logger.level = Logger::INFO

def test_email_discovery
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "🧪 TEST: Email Discovery Before Converting to Candidate"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  account = Account.where.not(ats_provider: nil).first
  if account.nil?
    puts "❌ No account with ATS provider found. Setting up account 1 with ATS..."
    account = Account.first
    account.update(ats_provider: "questt")
  end

  puts "✅ Using Account: #{account.name} (ID: #{account.id})"
  puts "   ATS Provider: #{account.ats_provider}"

  Apartment::Tenant.switch(account.tenant) do
    sourced_profile = SourcedProfile
      .where.not(external_id: nil)
      .where(candidate_id: nil)
      .order("RANDOM()")
      .first

    if sourced_profile.nil?
      puts "❌ No SourcedProfile without candidate found"
      return
    end

    puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "📋 SourcedProfile Selected:"
    puts "   ID: #{sourced_profile.id}"
    puts "   Name: #{sourced_profile.full_name}"
    puts "   External ID: #{sourced_profile.external_id}"
    puts "   Email (before): #{sourced_profile.email || 'NONE'}"
    puts "   Emails Array (before): #{sourced_profile.emails.inspect}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if sourced_profile.email.present?
      puts "\n⚠️  WARNING: Profile already has email. Clearing it for test..."
      sourced_profile.update_columns(email: nil, emails: [])
      sourced_profile.reload
      puts "   Email cleared successfully"
    end

    puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "🚀 Starting Conversion (will trigger email discovery)..."
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    result = SourcedProfiles::ConvertToCandidateService.call([ sourced_profile.id ])

    puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "📊 CONVERSION RESULT:"
    puts "   Success: #{result[:success]}"
    puts "   Converted: #{result[:converted]}"
    puts "   Skipped: #{result[:skipped]}"
    puts "   Failed: #{result[:failed]}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    sourced_profile.reload

    puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "📋 SourcedProfile After Conversion:"
    puts "   Email (after): #{sourced_profile.email || 'NONE'}"
    puts "   Emails Array (after): #{sourced_profile.emails.inspect}"
    puts "   Candidate ID: #{sourced_profile.candidate_id || 'NONE'}"
    puts "   Emails Enriched At: #{sourced_profile.emails_enriched_at || 'NONE'}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if sourced_profile.candidate_id.present?
      candidate = Candidate.find(sourced_profile.candidate_id)
      puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "👤 Candidate Created:"
      puts "   ID: #{candidate.id}"
      puts "   Name: #{candidate.name}"
      puts "   Email: #{candidate.email || 'NONE'}"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if sourced_profile.emails.present? && sourced_profile.emails_enriched_at.present?
      puts "✅ SUCCESS - Email was discovered via Pearch!"
      puts "   Email: #{sourced_profile.emails.first}"
      puts "   Enriched At: #{sourced_profile.emails_enriched_at}"
    elsif sourced_profile.emails.present?
      puts "⚠️  Email exists but was not enriched (might be from original data)"
    else
      puts "❌ FAILED - No email was discovered"
      puts "   Possible reasons:"
      puts "   - Insufficient Pearch credits"
      puts "   - Profile not found in Pearch database"
      puts "   - Invalid external_id"
    end
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end
end

begin
  test_email_discovery
rescue StandardError => e
  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "❌ ERROR: #{e.message}"
  puts "   #{e.backtrace.first(5).join("\n   ")}"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
end
