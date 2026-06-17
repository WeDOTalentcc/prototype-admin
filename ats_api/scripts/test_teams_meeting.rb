# frozen_string_literal: true

# Script de teste para criar meeting do Microsoft Teams
# Para executar no Rails console: load 'script/test_teams_meeting.rb'

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "🧪 TESTE: Criação de Meeting Microsoft Teams"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Buscar usuário pelo email corporativo
corporate_email = "anderson.victhor@talensesgroup.com"
personal_email = "victhor_root@hotmail.com"

puts "\n📧 Buscando usuário: #{corporate_email}"
user = User.find_by(email: corporate_email)

if user.nil?
  puts "❌ ERRO: Usuário não encontrado com email #{corporate_email}"
  puts "📋 Usuários disponíveis:"
  User.limit(5).pluck(:id, :email, :name).each do |id, email, name|
    puts "   - ID: #{id} | #{email} | #{name}"
  end
  exit
end

puts "✅ Usuário encontrado: #{user.name} (ID: #{user.id})"
puts "   Account: #{user.account.name} (ID: #{user.account_id})"
puts "   Tenant: #{user.account.tenant}"

# 2. Verificar conexão Microsoft
puts "\n🔐 Verificando conexão Microsoft..."
if user.microsoft_connected?
  puts "✅ Microsoft conectado!"
  puts "   Token expires at: #{user.ms_expires_at}"
  puts "   Token válido: #{user.ms_expires_at > Time.current ? 'SIM' : 'NÃO (vai renovar automaticamente)'}"
else
  puts "❌ ERRO: Microsoft não está conectado para este usuário"
  puts "   ms_access_token presente: #{user.ms_access_token.present?}"
  puts "   ms_refresh_token presente: #{user.ms_refresh_token.present?}"
  puts "   ms_expires_at: #{user.ms_expires_at}"
  puts "\n💡 Execute primeiro a autenticação OAuth do Microsoft para este usuário"
  exit
end

# 3. Configurar parâmetros do meeting
puts "\n📅 Configurando parâmetros do meeting..."
start_time = 15.minutes.from_now
end_time = start_time + 1.hour

meeting_params = {
  user: user,
  subject: "Teste de Meeting via API - #{Time.current.strftime('%H:%M')}",
  start_time: start_time,
  end_time: end_time,
  settings: {
    lobby_bypass_scope: 'organization',
    dial_in_bypass: false,
    allow_chat: 'enabled',
    allow_reactions: true,
    allowed_presenters: 'everyone',
    record_automatically: false,
    allow_attendee_mic: true,
    allow_attendee_camera: true
  }
}

puts "   Assunto: #{meeting_params[:subject]}"
puts "   Início: #{start_time.strftime('%d/%m/%Y %H:%M')}"
puts "   Fim: #{end_time.strftime('%d/%m/%Y %H:%M')}"
puts "   Duração: 60 minutos"

# 4. Criar meeting
puts "\n🚀 Criando meeting no Microsoft Teams..."
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

begin
  meeting = MeetingService.create(**meeting_params)

  puts "\n✅ SUCESSO! Meeting criado:"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "📋 Detalhes do Meeting:"
  puts "   ID no banco: #{meeting.id}"
  puts "   ID externo (Teams): #{meeting.external_id}"
  puts "   Provider: #{meeting.provider_text}"
  puts "   Status: #{meeting.status}"
  puts "   Organizador: #{meeting.organizer.name} (#{meeting.organizer.email})"
  puts ""
  puts "🔗 Link para participar:"
  puts "   #{meeting.join_url}"
  puts ""
  puts "📧 Você pode compartilhar este link com: #{personal_email}"
  puts ""
  puts "📊 Metadata completa:"
  puts meeting.metadata.to_json
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # 5. Teste de busca no Elasticsearch (se Meeting já foi indexado)
  puts "\n🔍 Testando busca no Elasticsearch..."
  begin
    results = Meeting.search(meeting.subject, limit: 1)
    if results.results.any?
      puts "✅ Meeting encontrado no Elasticsearch!"
    else
      puts "⚠️ Meeting ainda não indexado no ES (normal se for recém-criado)"
    end
  rescue => e
    puts "⚠️ Elasticsearch não disponível ou Meeting não indexado ainda: #{e.message}"
  end

  puts "\n✅ Teste concluído com sucesso!"

rescue MeetingService::ProviderNotAvailable => e
  puts "\n❌ ERRO: Provider não disponível"
  puts "   #{e.message}"

rescue MeetingService::MeetingCreationFailed => e
  puts "\n❌ ERRO: Falha ao criar meeting"
  puts "   #{e.message}"
  puts "\n💡 Possíveis causas:"
  puts "   - Token expirado (tente user.test_microsoft_refresh!)"
  puts "   - Permissões insuficientes no Azure AD"
  puts "   - Problemas de rede com Microsoft Graph API"

rescue => e
  puts "\n❌ ERRO INESPERADO"
  puts "   Classe: #{e.class}"
  puts "   Mensagem: #{e.message}"
  puts "   Backtrace:"
  e.backtrace.first(10).each { |line| puts "      #{line}" }
end

puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "🏁 Fim do teste"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
