# frozen_string_literal: true

namespace :ats do
  namespace :api_client do
    desc "Create a Python Agent ApiClient for an Account (ENV: ACCOUNT_NAME) — runs once"
    task create_python_agent: :environment do
      account_name = ENV["ACCOUNT_NAME"]
      unless account_name.present?
        puts 'ERR: Provide ACCOUNT_NAME env var. Example: ACCOUNT_NAME="Nome do Cliente"'
        exit 1
      end

      account = Account.find_by(name: account_name)
      unless account
        puts "Conta não encontrada: #{account_name}"
        exit 1
      end

      existing = ApiClient.find_by(account_id: account.id, name: "Python Agent")
      if existing
        puts "Já existe um ApiClient 'Python Agent' para a conta '#{account.name}'. Nada a fazer."
        puts "CLIENT_ID existente: #{existing.client_id}"
        exit 0
      end

      client_id = SecureRandom.hex(16)
      client_secret = SecureRandom.hex(32)
      secret_hash = BCrypt::Password.create(client_secret)

      api_client = ApiClient.create!(
        account: account,
        name: "Python Agent",
        client_id: client_id,
        client_secret_hash: secret_hash
      )

      puts "--- Credenciais para a conta: #{account.name} ---"
      puts "Armazene com segurança no Python:"
      puts "TENANT_ID: #{account.id}"
      puts "TENANT: #{account.tenant}"
      puts "CLIENT_ID: #{api_client.client_id}"
      puts "CLIENT_SECRET: #{client_secret}"
      puts "-------------------------------------------------"
    end
  end
end
