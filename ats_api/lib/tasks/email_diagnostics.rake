# frozen_string_literal: true

namespace :email do
  desc "Check Mailgun events for a specific recipient email"
  task :check_events, [ :recipient_email ] => :environment do |_t, args|
    require "net/http"
    require "uri"
    require "json"

    api_key = ENV.fetch("MAILGUN_KEY_API")
    domain = ENV.fetch("MAILGUN_DOMAIN", "mg.wedotalent.cc")
    recipient = args[:recipient_email]

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "🔍 Checking Mailgun events for: #{recipient || 'ALL'}"
    puts "   Domain: #{domain}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    uri = URI("https://api.mailgun.net/v3/#{domain}/events")
    params = { limit: 25 }
    params[:recipient] = recipient if recipient.present?
    uri.query = URI.encode_www_form(params)

    request = Net::HTTP::Get.new(uri)
    request.basic_auth("api", api_key)

    response = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) do |http|
      http.request(request)
    end

    if response.code != "200"
      puts "❌ API Error: #{response.code} — #{response.body}"
      next
    end

    data = JSON.parse(response.body)
    events = data["items"] || []

    if events.empty?
      puts "⚠️  No events found. Possible causes:"
      puts "   - Email was never sent"
      puts "   - Wrong domain (check if sending from different domain)"
      puts "   - Events expired (Mailgun keeps ~30 days)"
      next
    end

    events.each do |event|
      timestamp = Time.at(event["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
      event_type = event["event"]
      recipient_addr = event.dig("recipient") || event.dig("message", "headers", "to")
      subject = event.dig("message", "headers", "subject")
      severity = event["severity"]
      reason = event["reason"]
      delivery_status = event.dig("delivery-status")

      emoji = case event_type
      when "delivered" then "✅"
      when "accepted" then "📨"
      when "rejected" then "🚫"
      when "failed" then "❌"
      when "complained" then "⚠️"
      when "unsubscribed" then "🔕"
      when "opened" then "👀"
      when "clicked" then "🔗"
      else "📋"
      end

      puts ""
      puts "#{emoji} #{event_type.upcase} — #{timestamp}"
      puts "   To: #{recipient_addr}"
      puts "   Subject: #{subject}" if subject
      puts "   Severity: #{severity}" if severity
      puts "   Reason: #{reason}" if reason

      if delivery_status
        puts "   Delivery Status:"
        puts "     Code: #{delivery_status['code']}" if delivery_status["code"]
        puts "     Message: #{delivery_status['message']}" if delivery_status["message"]
        puts "     Description: #{delivery_status['description']}" if delivery_status["description"]
        puts "     Enhanced Code: #{delivery_status['enhanced-code']}" if delivery_status["enhanced-code"]
        puts "     MX Host: #{delivery_status['mx-host']}" if delivery_status["mx-host"]
        puts "     Session: #{delivery_status['session-seconds']}s" if delivery_status["session-seconds"]
      end
    end

    puts ""
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end

  desc "Check Mailgun bounces/suppressions for a recipient"
  task :check_suppressions, [ :recipient_email ] => :environment do |_t, args|
    require "net/http"
    require "uri"
    require "json"

    api_key = ENV.fetch("MAILGUN_KEY_API")
    domain = ENV.fetch("MAILGUN_DOMAIN", "mg.wedotalent.cc")
    recipient = args[:recipient_email]

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "🔍 Checking suppressions for: #{recipient || 'ALL'}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    %w[bounces complaints unsubscribes].each do |suppression_type|
      uri = if recipient.present?
              URI("https://api.mailgun.net/v3/#{domain}/#{suppression_type}/#{recipient}")
      else
              URI("https://api.mailgun.net/v3/#{domain}/#{suppression_type}")
      end

      request = Net::HTTP::Get.new(uri)
      request.basic_auth("api", api_key)

      response = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) do |http|
        http.request(request)
      end

      puts ""
      puts "📋 #{suppression_type.upcase}:"

      if response.code == "404"
        puts "   ✅ No #{suppression_type} found (clean)"
        next
      end

      if response.code != "200"
        puts "   ⚠️  API returned #{response.code}: #{response.body.first(200)}"
        next
      end

      data = JSON.parse(response.body)
      items = data["items"] || [ data ].compact

      if items.empty? || (items.length == 1 && items.first.keys == [ "message" ])
        puts "   ✅ No #{suppression_type} found (clean)"
      else
        items.each do |item|
          puts "   🚫 #{item['address'] || recipient}"
          puts "      Code: #{item['code']}" if item["code"]
          puts "      Error: #{item['error']}" if item["error"]
          puts "      Created: #{item['created_at']}" if item["created_at"]
        end
      end
    end

    puts ""
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end

  desc "Send a test email via SMTP with detailed logging"
  task :test_send, [ :to_email ] => :environment do |_t, args|
    to = args[:to_email]
    abort "Usage: rake email:test_send[user@example.com]" unless to.present?

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "🚀 Sending test email to: #{to}"
    puts "   From: #{ENV['MAILGUN_EMAIL']}"
    puts "   SMTP: #{ENV['MAILGUN_HOST']}:#{ENV['MAILGUN_PORT']}"
    puts "   Domain: #{ENV.fetch('MAILGUN_DOMAIN', 'mg.wedotalent.cc')}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    begin
      TestMailer.hello_email(to).deliver_now
      puts "✅ Email sent successfully via SMTP"
      puts "   Check Mailgun events in ~30s: rake email:check_events[#{to}]"
    rescue Net::SMTPAuthenticationError => e
      puts "❌ SMTP Auth Error: #{e.message}"
    rescue Net::SMTPServerBusy => e
      puts "❌ SMTP Server Busy: #{e.message}"
    rescue Net::SMTPFatalError => e
      puts "❌ SMTP Fatal Error: #{e.message}"
    rescue StandardError => e
      puts "❌ Error: #{e.class} — #{e.message}"
      puts e.backtrace.first(5).join("\n")
    end
  end

  desc "Send test email via Mailgun HTTP API (bypasses SMTP)"
  task :test_send_api, [ :to_email ] => :environment do |_t, args|
    require "net/http"
    require "uri"

    to = args[:to_email]
    abort "Usage: rake email:test_send_api[user@example.com]" unless to.present?

    api_key = ENV.fetch("MAILGUN_KEY_API")
    domain = ENV.fetch("MAILGUN_DOMAIN", "mg.wedotalent.cc")
    from = ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "🚀 Sending test via Mailgun HTTP API"
    puts "   To: #{to}"
    puts "   From: #{from}"
    puts "   Domain: #{domain}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    uri = URI("https://api.mailgun.net/v3/#{domain}/messages")
    request = Net::HTTP::Post.new(uri)
    request.basic_auth("api", api_key)
    request.set_form_data(
      "from" => "WeDO Talent <#{from}>",
      "to" => to,
      "subject" => "Teste Mailgun API — #{Time.current.strftime('%H:%M:%S')}",
      "text" => "Email de teste enviado via Mailgun HTTP API em #{Time.current}.",
      "o:tag" => "test-diagnostic"
    )

    response = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) do |http|
      http.request(request)
    end

    puts ""
    puts "Response: #{response.code}"
    puts response.body
    puts ""

    if response.code == "200"
      puts "✅ Mailgun accepted the message"
      puts "   Check delivery status in ~30s: rake email:check_events[#{to}]"
    else
      puts "❌ Mailgun rejected: #{response.code}"
    end
  end

  desc "Check DNS records (SPF, DKIM, DMARC) for the sending domain"
  task check_dns: :environment do
    domain = ENV.fetch("MAILGUN_DOMAIN", "mg.wedotalent.cc")

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "🔍 DNS Records for: #{domain}"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    puts "\n📋 SPF Record (TXT for #{domain}):"
    system("dig +short TXT #{domain} | grep -i spf || echo '   ⚠️  No SPF record found!'")

    puts "\n📋 DKIM Records:"
    %w[mailo._domainkey smtp._domainkey mx._domainkey k1._domainkey pic._domainkey].each do |selector|
      result = `dig +short TXT #{selector}.#{domain} 2>/dev/null`.strip
      puts "   #{selector}.#{domain}: #{result.present? ? result : '(not found)'}"
    end

    puts "\n📋 DMARC Record:"
    system("dig +short TXT _dmarc.#{domain} || echo '   ⚠️  No DMARC record found!'")

    puts "\n📋 MX Records:"
    system("dig +short MX #{domain} || echo '   ⚠️  No MX records found!'")

    puts "\n📋 Mailgun Domain Verification (via API):"
    api_key = ENV.fetch("MAILGUN_KEY_API", nil)
    if api_key
      require "net/http"
      require "uri"
      require "json"

      uri = URI("https://api.mailgun.net/v3/domains/#{domain}")
      request = Net::HTTP::Get.new(uri)
      request.basic_auth("api", api_key)

      response = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) do |http|
        http.request(request)
      end

      if response.code == "200"
        data = JSON.parse(response.body)
        domain_info = data["domain"] || {}
        puts "   State: #{domain_info['state']}"
        puts "   Type: #{domain_info['type']}"
        puts "   Created: #{domain_info['created_at']}"

        dns_records = data["sending_dns_records"] || []
        receiving_records = data["receiving_dns_records"] || []

        puts "\n   Sending DNS Records (expected by Mailgun):"
        dns_records.each do |record|
          status = record["valid"] == "valid" ? "✅" : "❌"
          puts "   #{status} #{record['record_type']} #{record['name']}"
          puts "      Value: #{record['value'].to_s.first(80)}"
          puts "      Valid: #{record['valid']}"
        end

        if receiving_records.any?
          puts "\n   Receiving DNS Records:"
          receiving_records.each do |record|
            status = record["valid"] == "valid" ? "✅" : "❌"
            puts "   #{status} #{record['record_type']} #{record['name']} → #{record['value']}"
          end
        end
      else
        puts "   ❌ Could not fetch domain info: #{response.code}"
        puts "   #{response.body.first(200)}"
      end
    else
      puts "   ⚠️  MAILGUN_KEY_API not set, skipping API check"
    end

    puts ""
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end

  desc "Full diagnostic: DNS + suppressions + events + test send"
  task :diagnose, [ :to_email ] => :environment do |_t, args|
    to = args[:to_email]
    abort "Usage: rake email:diagnose[user@microsoft-email.com]" unless to.present?

    Rake::Task["email:check_dns"].invoke
    puts "\n\n"
    Rake::Task["email:check_suppressions"].invoke(to)
    puts "\n\n"
    Rake::Task["email:check_events"].invoke(to)
    puts "\n\n"
    Rake::Task["email:test_send_api"].invoke(to)
  end
end
