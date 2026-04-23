# frozen_string_literal: true

namespace :teams do
  desc "Renew expiring Teams chat subscriptions (called by cron, safe to run manually)"
  task renew: :environment do
    MicrosoftService::TeamsSubscriptionService.renew_all_expiring
  end

  desc "Force recreate ALL active Teams chat subscriptions (use when subscriptions expired)"
  task recreate: :environment do
    MicrosoftService::TeamsSubscriptionService.renew_all_active
  end

  desc "Run full diagnostic of Teams subscriptions and connectivity"
  task diagnose: :environment do
    MicrosoftService::TeamsSubscriptionDiagnosticService.run
  end

  desc "Reset ALL Teams subscriptions (deletes from MS and recreates with new webhook URL)"
  task reset: :environment do
    puts "⚠️  This will DELETE and RECREATE all Teams subscriptions"
    puts "Current webhook URL: #{ENV['APP_HOST']}/v1/webhooks/teams_chat"
    print "Continue? (yes/no): "

    answer = STDIN.gets.chomp
    if answer.downcase == "yes"
      MicrosoftService::TeamsSubscriptionResetService.reset_all_subscriptions(force_delete_ms: true, verbose: true)
    else
      puts "❌ Aborted"
    end
  end

  desc "Reset subscriptions WITHOUT deleting from Microsoft (faster, may leave orphans)"
  task reset_fast: :environment do
    MicrosoftService::TeamsSubscriptionResetService.reset_all_subscriptions(force_delete_ms: false, verbose: true)
  end

  desc "NUKE: Delete ALL MS subscriptions (including orphans) and recreate from scratch"
  task nuke: :environment do
    puts "💣 This will query Microsoft for ALL subscriptions, delete them, and recreate"
    puts "   Webhook URL: #{ENV['APP_HOST']}/v1/webhooks/teams_chat"
    puts ""
    MicrosoftService::TeamsSubscriptionResetService.nuke_and_recreate(verbose: true)
  end

  desc "Show status of all Teams chat subscriptions across tenants"
  task status: :environment do
    Account.pluck(:tenant).each do |tenant|
      Apartment::Tenant.switch(tenant) do
        next unless ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)

        subs = TeamsChatSubscription.all
        next if subs.empty?

        puts "\n=== Tenant: #{tenant} (#{subs.count} subscriptions) ==="
        subs.find_each do |s|
          expires = s.subscription_expires_at&.strftime("%Y-%m-%d %H:%M:%S UTC")
          active = s.subscription_active? ? "ACTIVE" : "INACTIVE"
          puts "  [#{active}] chat=#{s.chat_id} status=#{s.status} expires=#{expires} lia_user=#{s.lia_user_id}"
        end
      end
    end
  end

  desc "Auto-reset for cron (silent, logs only to Rails.logger)"
  task auto_reset: :environment do
    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Rails.logger.info "🔄 [Cron] Teams Auto Reset - Starting"
    Rails.logger.info "   APP_HOST: #{ENV.fetch('APP_HOST', 'NOT_SET')}"
    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    result = MicrosoftService::TeamsSubscriptionResetService.nuke_and_recreate(verbose: false)

    if result[:recreated] > 0 || result[:failed] == 0
      Rails.logger.info "✅ [Cron] Reset completed: #{result[:recreated]} recreated, #{result[:failed]} failed"
    else
      Rails.logger.error "❌ [Cron] Reset failed: #{result[:errors].join(', ')}"
    end

    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end

  desc "Retry all failed subscriptions"
  task retry_failed: :environment do
    puts "🔄 Retrying all failed subscriptions..."
    MicrosoftService::TeamsSubscriptionService.retry_all_failed
    puts "✅ Done"
  end

  desc "Send proactive greeting from LIA to all users of a domain (e.g. wedotalent.cc)"
  task :outreach, [ :domain ] => :environment do |_t, args|
    domain = args[:domain] || "wedotalent.cc"
    puts "🚀 Sending proactive Teams messages to all @#{domain} users"
    puts "   This will CREATE new 1:1 chats and register webhook subscriptions"
    puts ""

    result = MicrosoftService::TeamsProactiveOutreachService.call(domain: domain)

    puts ""
    puts "═══════════════════════════════════════════════════"
    puts "✅ Outreach completed"
    puts "   Enqueued: #{result[:sent]}"
    puts "   Skipped (already have chat): #{result[:skipped]}"
    puts "   Failed: #{result[:failed]}"
    puts "═══════════════════════════════════════════════════"
  end

  desc "Dry-run proactive outreach — shows who would receive messages without sending"
  task :outreach_dry_run, [ :domain ] => :environment do |_t, args|
    domain = args[:domain] || "wedotalent.cc"
    puts "🔍 [DRY RUN] Checking @#{domain} users who would receive proactive messages"
    puts ""

    result = MicrosoftService::TeamsProactiveOutreachService.call(domain: domain, dry_run: true)

    puts ""
    puts "═══════════════════════════════════════════════════"
    puts "🔍 Dry run completed"
    puts "   Would send: #{result[:sent]}"
    puts "   Already have chat: #{result[:skipped]}"
    puts "═══════════════════════════════════════════════════"
  end
end
