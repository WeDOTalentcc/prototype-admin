#!/bin/bash

echo "🧪 Testando LIA Agent System"
echo ""

# Health check
echo "1️⃣ Testando Health Check..."
curl -s http://localhost:8000/health | jq . || echo "❌ API não está respondendo"

echo ""
echo ""

# Primeiro chat
echo "2️⃣ Enviando primeira mensagem para LIA..."
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Oi LIA, tudo bem?"
  }')

echo "$RESPONSE" | jq .

echo ""
echo ""

# Extrair conversation_id
CONVERSATION_ID=$(echo "$RESPONSE" | jq -r '.conversation.id')

if [ "$CONVERSATION_ID" != "null" ]; then
    echo "✅ Conversação criada: $CONVERSATION_ID"
    echo ""
    echo "3️⃣ Enviando segunda mensagem..."
    echo ""
    
    curl -s -X POST http://localhost:8000/api/v1/chat \
      -H "Content-Type: application/json" \
      -d "{
        \"content\": \"Preciso criar uma vaga de desenvolvedor Python sênior\",
        \"conversation_id\": \"$CONVERSATION_ID\"
      }" | jq .
    
    echo ""
    echo ""
    echo "✅ Teste completo!"
else
    echo "❌ Erro ao criar conversação"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Ver todas conversas:"
echo "curl http://localhost:8000/api/v1/chat/conversations?user_id=demo-user | jq ."
echo ""
echo "📚 Documentação completa:"
echo "http://localhost:8000/docs"
