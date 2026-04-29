# frozen_string_literal: true

#
# Microsoft Graph - Device Code Flow
# Não precisa de redirect URI, funciona direto no terminal
#
# Execute: load 'scripts/ms_device_auth.rb'

require 'net/http'
require 'uri'
require 'json'

DEVICE_CODE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
TOKEN_URL_DEVICE = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

SCOPES = [
  'offline_access',
  'User.Read',
  'Mail.Read',
  'Mail.ReadWrite',
  'Mail.Send',
  'MailboxSettings.Read',
  'Calendars.ReadWrite',
  'OnlineMeetings.ReadWrite',
  'Tasks.ReadWrite',
  'Chat.ReadWrite',
  'Chat.Create'
].join(' ')

def device_http_post(url, params)
  uri = URI(url)
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = true
  http.read_timeout = 30
  request = Net::HTTP::Post.new(uri)
  request['Content-Type'] = 'application/x-www-form-urlencoded'
  request.body = URI.encode_www_form(params)
  response = http.request(request)
  JSON.parse(response.body)
end

puts "\n" + "━" * 60
puts "🔐 Microsoft Graph - Device Code Flow"
puts "━" * 60

client_id = ENV.fetch('AZURE_APP_ID')

device_resp = device_http_post(DEVICE_CODE_URL, {
  client_id: client_id,
  scope: SCOPES
})

if device_resp['error']
  puts "❌ Erro ao iniciar device flow: #{device_resp['error']}"
  puts "   #{device_resp['error_description']}"
  return
end

puts "\n📋 Instruções:"
puts "   1. Abra no browser: #{device_resp['verification_uri']}"
puts "   2. Digite o código: #{device_resp['user_code']}"
puts "   3. Faça login com: anderson.victhor@talensesgroup.com"
puts "\n⏳ Aguardando autorização (#{device_resp['expires_in']}s)..."
puts "━" * 60

device_code = device_resp['device_code']
interval = device_resp['interval'] || 5
expires_in = device_resp['expires_in'] || 900
deadline = Time.now + expires_in

token_resp = nil
loop do
  sleep(interval)

  resp = device_http_post(TOKEN_URL_DEVICE, {
    client_id: client_id,
    grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
    device_code: device_code
  })

  if resp['access_token']
    token_resp = resp
    break
  elsif resp['error'] == 'authorization_pending'
    print "."
    $stdout.flush
  elsif resp['error'] == 'slow_down'
    interval += 5
  else
    puts "\n❌ Erro: #{resp['error']} - #{resp['error_description']}"
    break
  end

  if Time.now > deadline
    puts "\n❌ Tempo esgotado. Tente novamente."
    break
  end
end

if token_resp
  user = User.find_by(email: 'anderson.victhor@talensesgroup.com')
  expires_at = Time.current + token_resp['expires_in'].to_i.seconds - 5.minutes

  user.update!(
    ms_access_token: token_resp['access_token'],
    ms_refresh_token: token_resp['refresh_token'],
    ms_expires_at: expires_at
  )

  puts "\n✅ Tokens salvos com sucesso!"
  puts "   ms_access_token: #{token_resp['access_token'][0, 20]}..."
  puts "   ms_refresh_token: #{token_resp['refresh_token']&.[](0, 20)}..."
  puts "   expires_at: #{expires_at}"
  puts "\n▶ Execute: load 'scripts/test_teams_meeting.rb'"
end
