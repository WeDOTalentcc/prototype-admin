# Fluxo de Criação de Mensagens no Domínio sourced_profile_sourcing

## Visão Geral

Este documento descreve como as mensagens são criadas e enviadas para os usuários no domínio `sourced_profile_sourcing`, garantindo que **todas as respostas** (sucesso ou falha) sejam notificadas via API.

## Arquitetura de Criação de Mensagens

### Fluxo Principal (Recomendado)

```
1. Task (process_query) 
   ↓
2. DomainOrchestrator.process_query()
   ↓
3. DomainWorkflow.process()
   ↓
4. Domain.execute_action() ou Agent.process()
   ↓
5. Retorna DomainResponse/AgentResponse
   ↓  
6. DomainOrchestrator cria mensagem via _create_domain_message()
```

**Este é o fluxo padrão e SEMPRE cria mensagens.**

### Componentes Responsáveis

#### 1. DomainOrchestrator (`src/domains/orchestrator.py`)

Responsável por:
- Processar queries de todos os domínios
- Chamar o workflow apropriado
- **CRIAR MENSAGENS** via API para notificar usuários
- Tratar exceções e criar mensagens de erro

```python
if domain_id == "sourced_profile_sourcing":
    if not context.user_id:
        logger.warning("Skipping message creation: missing user_id")
    else:
        self._create_domain_message(
            user_id=context.user_id,
            content=response.message,
            metadata=msg_metadata,
            domain_reference_id=context.sourcing_id,
            workspace_id=context.workspace_id
        )
```

#### 2. Actions/Agents

Responsáveis por:
- Processar a query específica
- Buscar dados via API
- Formatar resposta
- **NÃO criam mensagens diretamente** (retornam DomainResponse/AgentResponse)

### Quando Mensagens SÃO Criadas

✅ **SEMPRE** que:
- Uma query é processada com sucesso
- Uma query falha (com erro)
- Uma clarificação é necessária
- Não encontra candidatos
- Encontra candidatos
- Qualquer resposta do domínio sourced_profile_sourcing

### Quando Mensagens NÃO São Criadas

❌ **APENAS se**:
- `context.user_id` está vazio/None (log de warning é gerado)
- Erro crítico antes do bloco try no orchestrator

## Criação Direta de Mensagens pelos Agents (Opcional)

Os agents têm um método utilitário caso precisem criar mensagens adicionais:

```python
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent

class MyAgent(BaseAgent):
    def process(self, query, context, aggregated_stats, params):
        # Processamento normal...
        
        # Criar mensagem adicional (opcional)
        self.create_user_message(
            context=context,
            content="Mensagem adicional específica",
            metadata={"action": "specific_notification"},
            success=True
        )
        
        # Retornar resposta normal (orchestrator criará mensagem principal)
        return AgentResponse(success=True, message="...")
```

**⚠️ CUIDADO:** Use apenas quando necessário notificar o usuário de eventos intermediários ou ações paralelas. O orchestrator **sempre** cria a mensagem final.

## Logs de Debug

### Logs do Orchestrator
```
[API] Skipping message creation: missing user_id | sourcing_id=1014
[API] Enviando resposta para usuário 1 via wedotalent | sourcing_id=1014
[API] ✓ Message criada com sucesso para user_id=1 | sourcing_id=1014
[API] ✗ Falha ao criar message: HTTP 401
```

### Logs do API Client
```
[API] create_message | user_id=1 | domain_ref=1014 | content_len=250
[API] create_message: missing user_id
[API] create_message: empty content
[API] create_message OK | user_id=1 | domain_ref=1014 | id=2028
[API] create_message HTTP 400: Invalid user_id
```

### Logs dos Agents
```
[search] ✓ Message created | user_id=1 | sourcing_id=1014
[search] Cannot create message: missing user_id | sourcing_id=1014
[search] ✗ Failed to create message: HTTP 401
```

## Cenários Específicos

### 1. Busca SEM Resultados
```
Query: "Pesquisa para mim quem é Stephen Janero fazendo"
Resultado: 0 candidatos encontrados
Mensagem: ✅ CRIADA com "❌ Nenhum candidato encontrado com nome 'Stephen Janero'"
```

### 2. Busca COM Resultados
```
Query: "Top 10 candidatos"
Resultado: 10 candidatos retornados
Mensagem: ✅ CRIADA com tabela formatada dos candidatos
```

### 3. Erro de Processamento
```
Query: qualquer
Resultado: Exception capturada
Mensagem: ✅ CRIADA com "❌ Erro ao processar sua pergunta"
```

### 4. Clarificação Necessária
```
Query: ambígua
Resultado: needs_clarification=True
Mensagem: ✅ CRIADA com opções para o usuário escolher
```

## Troubleshooting

### Mensagem não foi criada?

1. **Verificar logs**: Procure por `[API] Skipping message creation`
2. **user_id presente?**: Context deve ter `user_id` válido
3. **sourcing_id válido?**: Domain valida presença de sourcing_id
4. **Exceção antes do try?**: Logs de erro antes do workflow

### Mensagem duplicada?

- **NÃO use** `create_user_message()` nos agents a menos que seja mensagem adicional/paralela
- O orchestrator **sempre** cria a mensagem final

### Validar fluxo completo

```bash
# Buscar logs de uma mensagem específica
grep "message_id=2027" logs/app.log

# Verificar se mensagem foi criada
grep "create_message OK" logs/app.log | grep "user_id=1"

# Identificar mensagens que falharam
grep "create_message HTTP" logs/app.log | grep -v "200\|201"
```

## Checklist para Novas Actions/Agents

- [ ] Retornar `DomainResponse` ou `AgentResponse` (nunca criar mensagem diretamente)
- [ ] Incluir `success=True/False` apropriado
- [ ] Adicionar metadata relevante na resposta
- [ ] Incluir `suggestions` quando útil
- [ ] Formatar mensagem com markdown
- [ ] Logar processos importantes
- [ ] Tratar exceções adequadamente

## Conclusão

O sistema **GARANTE** que todas as respostas do domínio `sourced_profile_sourcing` criem mensagens via API para notificar o usuário, independentemente de:
- Encontrar ou não encontrar candidatos
- Sucesso ou falha da operação
- Tipo de action executada
- Agent específico que processou

As mensagens são criadas pelo **DomainOrchestrator** após o processamento, mantendo separação de responsabilidades e consistência em todo o sistema.
