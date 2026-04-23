# frozen_string_literal: true

# Gera o URL de autorização Microsoft OAuth para conectar a integração
# Execute no Rails console: load 'scripts/generate_ms_auth_url.rb'

require 'cgi'

user = User.find_by(email: "anderson.victhor@talensesgroup.com")

scopes = [
  'openid', 'profile', 'email', 'offline_access',
  'User.Read', 'Mail.Read', 'Mail.ReadWrite', 'Mail.Send',
  'MailboxSettings.Read', 'Calendars.ReadWrite',
  'OnlineMeetings.ReadWrite', 'Tasks.ReadWrite',
  'Chat.ReadWrite', 'Chat.Create'
].join(' ')

state_payload = { user_id: user.id, exp: 10.minutes.from_now.to_i }
state_token = JWT.encode(state_payload, Rails.application.secret_key_base)

callback_url = "http://localhost:8080/v1/auth/microsoft_graph_auth/callback"

url  = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
url += "client_id=#{ENV['AZURE_APP_ID']}&"
url += "redirect_uri=#{CGI.escape(callback_url)}&"
url += "response_type=code&"
url += "scope=#{CGI.escape(scopes)}&"
url += "state=#{state_token}"

puts "\n" + "━" * 70
puts "🔗 Abra esta URL no navegador para autorizar a integração Microsoft:"
puts "━" * 70
puts url
puts "━" * 70
puts "\nApós autorizar, os campos ms_access_token/ms_refresh_token serão preenchidos."
puts "Depois execute: load 'scripts/test_teams_meeting.rb'"
