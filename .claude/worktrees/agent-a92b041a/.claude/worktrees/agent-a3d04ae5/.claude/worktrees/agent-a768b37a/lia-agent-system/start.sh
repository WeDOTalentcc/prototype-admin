#!/bin/bash

echo "🚀 Iniciando LIA Agent System..."
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Erro: Arquivo .env não encontrado!"
    echo "📝 Copie .env.example para .env e configure suas API keys"
    exit 1
fi

# Verificar se ANTHROPIC_API_KEY está configurada
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env; then
    echo "⚠️  Aviso: ANTHROPIC_API_KEY não configurada no .env"
    echo "📝 Edite o arquivo .env e adicione sua Claude API key"
    exit 1
fi

echo "✅ Arquivo .env encontrado"
echo ""

# Iniciar serviços Docker
echo "📦 Iniciando PostgreSQL, Redis e RabbitMQ..."
docker-compose up -d postgres redis rabbitmq

echo ""
echo "⏳ Aguardando serviços ficarem prontos (15 segundos)..."
sleep 15

echo ""
echo "🔍 Verificando status dos serviços..."
docker-compose ps

echo ""
echo "✅ Serviços iniciados!"
echo ""

# Verificar se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual Python..."
    python3 -m venv venv
    echo "✅ Ambiente virtual criado"
    echo ""
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "🗄️  Verificando banco de dados..."

# Verificar se migration já foi criada
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "📝 Criando migração inicial..."
    alembic revision --autogenerate -m "Initial migration"
fi

# Aplicar migrations
echo "🔄 Aplicando migrations..."
alembic upgrade head

echo ""
echo "🎉 Tudo pronto!"
echo ""
echo "🚀 Iniciando API FastAPI..."
echo "📍 Acesse: http://localhost:8000/docs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Iniciar API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
