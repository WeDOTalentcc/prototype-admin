#!/bin/bash
# frozen_string_literal: true

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing Gemini Models (Docker)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose exec web rails runner "
models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
client = GeminiClient.new

models.each do |model|
  print \"🔍 Testing #{model}... \"
  begin
    response = client.chat(
      model: model,
      messages: [{ role: 'user', content: 'Say OK if you work.' }],
      temperature: 0.1,
      max_tokens: 50
    )
    content = response.dig('choices', 0, 'message', 'content')
    puts \"✅ SUCCESS - Response: #{content.to_s.strip.first(50)}\"
  rescue => e
    puts \"❌ FAILED - #{e.message}\"
  end
end
"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
