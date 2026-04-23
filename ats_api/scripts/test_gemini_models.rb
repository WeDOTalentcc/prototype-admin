# frozen_string_literal: true

def test_gemini_models
  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "🧪 Testing Gemini Models"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
  ]

  client = GeminiClient.new

  models.each do |model|
    print "\n🔍 Testing #{model}... "

    begin
      response = client.chat(
        model: model,
        messages: [ { role: "user", content: "Say 'OK' if you work." } ],
        temperature: 0.1,
        max_tokens: 50
      )

      content = response.dig("choices", 0, "message", "content")
      puts "✅ SUCCESS - Response: #{content.to_s.strip.first(50)}"
    rescue => e
      error_msg = e.message.to_s
      if error_msg.include?("404")
        puts "❌ FAILED - 404 (model not found/deprecated)"
      else
        puts "❌ FAILED - #{error_msg.first(80)}"
      end
    end
  end

  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
end

test_gemini_models
