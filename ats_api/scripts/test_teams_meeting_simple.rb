# TESTE RÁPIDO - COPY/PASTE NO RAILS CONSOLE
# ============================================

# 1. Buscar seu usuário
user = User.find_by(email: "anderson.victhor@talensesgroup.com")

# 2. Verificar se Microsoft está conectado
puts "Microsoft conectado: #{user.microsoft_connected?}"
puts "Token expira em: #{user.ms_expires_at}"

# 3. Criar meeting de teste (se conectado)
if user.microsoft_connected?
  meeting = MeetingService.create(
    user: user,
    subject: "Teste Teams Meeting - #{Time.current.strftime('%H:%M')}",
    start_time: 15.minutes.from_now,
    end_time: 1.hour.from_now + 15.minutes,
    settings: {
      lobby_bypass_scope: 'organization',
      allow_chat: 'enabled',
      allowed_presenters: 'everyone',
      record_automatically: false
    }
  )

  puts "\n✅ Meeting criado!"
  puts "ID: #{meeting.id}"
  puts "Provider: #{meeting.provider_text}"
  puts "Link: #{meeting.join_url}"
  puts "\n📧 Compartilhe este link com: victhor_root@hotmail.com"
else
  puts "❌ Microsoft não conectado. Execute primeiro a autenticação OAuth."
end
