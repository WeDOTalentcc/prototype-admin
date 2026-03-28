# Guia de Prompts LIA

Este documento descreve as convenções, estrutura e processo para criar e manter prompts no sistema LIA.

## Índice

1. [Estrutura de Arquivos](#estrutura-de-arquivos)
2. [Convenções de Nomenclatura](#convenções-de-nomenclatura)
3. [Estrutura Padrão de Prompt](#estrutura-padrão-de-prompt)
4. [Como Criar um Novo Prompt](#como-criar-um-novo-prompt)
5. [Versionamento](#versionamento)
6. [Processo de Revisão](#processo-de-revisão)
7. [Boas Práticas](#boas-práticas)

---

## Estrutura de Arquivos

```
lia-agent-system/app/agents/prompts/
├── __init__.py              # Exports públicos
├── agent_prompts.py         # Definições dos prompts
├── prompt_registry.py       # Sistema de versionamento
├── README.md                # Este arquivo
└── examples/                # Exemplos de uso
    └── ...
```

---

## Convenções de Nomenclatura

### Nomes de Prompts

| Convenção | Exemplo | Descrição |
|-----------|---------|-----------|
| Constante | `ORCHESTRATOR_PROMPT` | SCREAMING_SNAKE_CASE |
| Chave do registry | `"orchestrator"` | snake_case sem sufixo |
| Agente | `Orquestrador Central` | Nome amigável em português |

### Padrões de Nomes

```python
# Constantes de prompt
{AGENT_NAME}_PROMPT = """..."""

# Componentes compartilhados
LIA_PERSONA = """..."""
HR_VOCABULARY = """..."""
DATA_PERSISTENCE_GUIDELINES = """..."""
ETHICAL_GUIDELINES = """..."""
```

### Chaves no Registry

```python
prompt_registry.register_prompt(
    name="nome_do_agente",      # snake_case
    content=NOME_DO_AGENTE_PROMPT,
    version="X.Y.Z",
    author="nome_autor",
    changelog="Descrição da mudança"
)
```

---

## Estrutura Padrão de Prompt

Todo prompt de agente deve seguir esta estrutura:

```python
AGENT_NAME_PROMPT = f"""{LIA_PERSONA}

{ETHICAL_GUIDELINES}  # Se aplicável

Você é o Agente [N] da LIA - [Nome do Agente].

## Sua Identidade
- Nome: [Nome]
- Papel: [Descrição do papel]
- Expertise: [Áreas de especialização]

## Vocabulário Esperado nas Respostas
Use naturalmente estes termos técnicos de RH:
- **[Categoria]**: [termos]
- **[Categoria]**: [termos]

## Suas Responsabilidades
- [Responsabilidade 1]
- [Responsabilidade 2]
- [Responsabilidade 3]

## [Seção Específica do Agente]
[Conteúdo específico: metodologias, fluxos, etc.]

## Persistência de Dados (OBRIGATÓRIO)
Ao [ação principal], SEMPRE:
1. **[Ação de persistência 1]**
2. **[Ação de persistência 2]**
3. **[Ação de persistência 3]**

### Dados a Persistir:
| Dado | Campo WedoTalent | Sync ATS |
|------|------------------|----------|
| [dado] | [campo] | Sim/Não |

## Formato de Resposta Estruturada

### Para [Tipo de Resposta 1]:
```
[Emoji] **[Título]**

**[Seção 1]**
[Conteúdo]

**[Seção 2]**
[Conteúdo]

💾 **Persistência**
- [Status de persistência]
```

## Contexto Atual
{{context}}"""
```

### Seções Obrigatórias

1. **Persona LIA**: Incluir `{LIA_PERSONA}` no início
2. **Identidade**: Nome, papel, expertise
3. **Vocabulário**: Termos técnicos de RH esperados
4. **Responsabilidades**: Lista clara de funções
5. **Persistência de Dados**: Regras de salvamento
6. **Formato de Resposta**: Templates estruturados
7. **Contexto**: Placeholder `{context}` no final

### Seções Opcionais

- **Diretrizes Éticas**: `{ETHICAL_GUIDELINES}` para agentes de avaliação
- **Metodologias**: Para agentes com métodos específicos
- **Integrações**: Para agentes que conectam sistemas
- **Fluxos**: Para agentes com processos definidos

---

## Como Criar um Novo Prompt

### Passo 1: Definir a Constante

Em `agent_prompts.py`:

```python
NEW_AGENT_PROMPT = f"""{LIA_PERSONA}

Você é o Agente [N] da LIA - [Nome].

## Sua Identidade
...

## Contexto Atual
{{context}}"""
```

### Passo 2: Registrar no Registry

Em `prompt_registry.py`, adicionar em `init_prompts()`:

```python
from app.agents.prompts.agent_prompts import NEW_AGENT_PROMPT

prompt_registry.register_prompt(
    name="new_agent",
    content=NEW_AGENT_PROMPT,
    version="1.0.0",
    author="seu_nome",
    changelog="Initial version - Agente para [propósito]"
)
```

### Passo 3: Adicionar ao get_agent_prompt

```python
def get_agent_prompt(agent_type: str, context: str = "") -> str:
    prompts = {
        # ... prompts existentes
        "new_agent": NEW_AGENT_PROMPT,
    }
    # ...
```

### Passo 4: Documentar no Catálogo

Adicionar entrada em `lia-agent-system/docs/PROMPTS_CATALOG.md`.

### Passo 5: Testar

```python
from app.agents.prompts import get_agent_prompt

prompt = get_agent_prompt("new_agent", context="Contexto de teste")
print(prompt)
```

---

## Versionamento

### Formato Semântico

Usamos [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

Exemplos:
1.0.0 - Versão inicial
1.1.0 - Nova funcionalidade (compatível)
1.1.1 - Correção de bug
2.0.0 - Mudança incompatível
```

### Quando Incrementar

| Mudança | Versão | Exemplo |
|---------|--------|---------|
| Correção de typo | PATCH | 2.0.0 → 2.0.1 |
| Melhoria de clareza | PATCH | 2.0.1 → 2.0.2 |
| Nova seção adicionada | MINOR | 2.0.2 → 2.1.0 |
| Novo formato de resposta | MINOR | 2.1.0 → 2.2.0 |
| Mudança de estrutura completa | MAJOR | 2.2.0 → 3.0.0 |
| Mudança de comportamento | MAJOR | 2.2.0 → 3.0.0 |

### Registro de Versão

```python
prompt_registry.register_prompt(
    name="orchestrator",
    content=ORCHESTRATOR_PROMPT,
    version="2.1.0",
    author="joao.silva",
    changelog="Adicionada seção de handling de erros"
)
```

---

## Processo de Revisão

### Checklist de Revisão

Antes de submeter um prompt para revisão:

- [ ] Segue a estrutura padrão
- [ ] Inclui persona LIA
- [ ] Inclui vocabulário técnico de RH
- [ ] Inclui seção de persistência de dados
- [ ] Inclui formato de resposta estruturada
- [ ] Usa placeholder `{context}`
- [ ] Não contém erros gramaticais
- [ ] Testado com contextos variados
- [ ] Documentado no catálogo
- [ ] Versionado corretamente

### Fluxo de Aprovação

```
1. Criar/Modificar prompt
    ↓
2. Auto-revisão (checklist)
    ↓
3. Teste local
    ↓
4. Pull Request
    ↓
5. Code Review (2 aprovações)
    ↓
6. Merge para main
    ↓
7. Atualizar catálogo
```

### Critérios de Aprovação

1. **Clareza**: O prompt é claro e sem ambiguidade?
2. **Completude**: Todas as seções obrigatórias estão presentes?
3. **Consistência**: Segue o padrão dos outros prompts?
4. **Eficácia**: Produz respostas de qualidade?
5. **Persistência**: Regras de dados estão completas?

---

## Boas Práticas

### DO (Faça)

```python
# Use f-strings para compor prompts
PROMPT = f"""{LIA_PERSONA}
{ETHICAL_GUIDELINES}
...
"""

# Use tabelas para dados estruturados
| Campo | Valor | Descrição |
|-------|-------|-----------|

# Use emojis para formatação visual
📋 **Título**
✅ Sucesso
⚠️ Atenção
❌ Erro

# Inclua exemplos de formato de resposta
### Para [Tipo]:
```
[formato]
```
```

### DON'T (Não Faça)

```python
# Não use strings longas sem formatação
PROMPT = "Você é um agente que faz X e Y e Z..."

# Não omita seções obrigatórias
PROMPT = """
## Identidade
...
# Faltando: Persistência, Formato, etc.
"""

# Não use linguagem informal
"Fala aí, beleza? Vou te ajudar..."

# Não hardcode contextos
"Para a vaga de Desenvolvedor Python..."  # Usar {context}
```

### Linguagem

- Use português brasileiro formal
- Evite anglicismos desnecessários
- Use termos do vocabulário HR padronizado
- Seja inclusivo (evite gênero quando possível)

### Performance

- Mantenha prompts concisos mas completos
- Use tabelas para dados estruturados (mais eficiente)
- Evite repetição de instruções
- Reutilize componentes compartilhados

---

## Exemplos

### Exemplo Completo de Prompt

```python
EXAMPLE_AGENT_PROMPT = f"""{LIA_PERSONA}

{ETHICAL_GUIDELINES}

Você é o Agente 12 da LIA - Especialista em Onboarding.

## Sua Identidade
- Nome: Onboarding Specialist
- Papel: Especialista em integração de novos colaboradores
- Expertise: Onboarding, documentação, período de experiência

## Vocabulário Esperado nas Respostas
Use naturalmente estes termos técnicos de RH:
- **Onboarding**: integração, período de experiência, documentação
- **Processo**: check-in, acompanhamento, mentoria
- **Status**: em integração, concluído, em acompanhamento

## Suas Responsabilidades
- Coordenar processo de onboarding
- Gerar checklist de documentação
- Agendar check-ins de acompanhamento
- Monitorar período de experiência

## Persistência de Dados (OBRIGATÓRIO)
Ao gerenciar onboarding, SEMPRE:
1. **Registrar data de início** no perfil do candidato
2. **Criar checklist** de onboarding
3. **Atualizar status** para "Em Onboarding"

### Dados a Persistir:
| Dado | Campo WedoTalent | Sync ATS |
|------|------------------|----------|
| Data início | start_date | Sim |
| Status | onboarding_status | Sim |
| Checklist | onboarding_checklist | Não |

## Formato de Resposta Estruturada

### Para Início de Onboarding:
```
🎉 **Onboarding Iniciado**

**Novo Colaborador**: [Nome]
**Cargo**: [Título]
**Data de Início**: [Data]

**Checklist de Documentação**
- [ ] Contrato assinado
- [ ] Documentos pessoais
- [ ] Dados bancários

💾 **Persistência**
- Perfil atualizado: ✅
- Status sincronizado: ✅
```

## Contexto Atual
{{context}}"""
```

---

## Suporte

Para dúvidas sobre prompts:
- Consulte o [Catálogo de Prompts](../../docs/PROMPTS_CATALOG.md)
- Abra uma issue no repositório
- Contate o time de IA
