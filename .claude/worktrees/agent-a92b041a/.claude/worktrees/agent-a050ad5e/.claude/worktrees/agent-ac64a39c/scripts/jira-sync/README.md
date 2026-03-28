# Jira Sync - Sincronização de Cards do Jira

Sistema para sincronizar cards do Jira a partir de arquivos Markdown (.md).

## Instalação

```bash
cd scripts/jira-sync
pip install -r requirements.txt
```

## Configuração

Configure as seguintes variáveis de ambiente:

```bash
export JIRA_EMAIL="seu-email@empresa.com"
export JIRA_API_TOKEN="seu-token-aqui"
export JIRA_BASE_URL="https://wedotalent.atlassian.net"  # opcional
export JIRA_PROJECT_KEY="WT"  # opcional
```

### Como obter o API Token do Jira

1. Acesse: https://id.atlassian.com/manage-profile/security/api-tokens
2. Clique em "Create API token"
3. Dê um nome (ex: "Jira Sync")
4. Copie o token gerado

## Uso

### Listar arquivos disponíveis

```bash
python sync.py list
```

Mostra todos os arquivos .md que contêm cards Jira na pasta `docs/`.

### Preview da sincronização

```bash
python sync.py preview docs/configuracoes-admin-cards-jira.md
```

Mostra quais cards serão criados ou atualizados, sem fazer alterações.

### Sincronizar cards

```bash
# Com confirmação
python sync.py sync docs/configuracoes-admin-cards-jira.md

# Sem confirmação
python sync.py sync docs/configuracoes-admin-cards-jira.md --yes
```

## Estrutura dos Arquivos .md

Os arquivos devem conter blocos YAML com a seguinte estrutura:

```markdown
### CARD EMP-001: Nome do Card

```yaml
Titulo: [FULL-STACK] Descrição do card
Tipo: Feature
Sprint: 1
Pontos: 8
Prioridade: Alta
Epic: EPIC-SET-002
Dependencias: EMP-000

Descricao: |
  Descrição detalhada do card.

Historia de Usuario: |
  Como usuário, eu quero...

Regras de Negocio:
  1. Regra 1
  2. Regra 2

Requisitos Tecnicos:
  Backend:
    - Endpoint X
    - Endpoint Y
  Frontend:
    - Componente A
    - Componente B

DoD:
  - [ ] Critério 1
  - [ ] Critério 2

Criterios de Aceitacao:
  - [ ] Aceitação 1
  - [ ] Aceitação 2
```
```

## Campos Mapeados

| Campo YAML | Campo Jira |
|------------|------------|
| Titulo | Summary |
| Tipo | Issue Type (Story, Task, Bug) |
| Prioridade | Priority |
| Pontos | Story Points (customfield) |
| Epic | Epic Link |
| Descrição + todas as seções | Description |

## Labels Geradas

- `card-id:EMP-001` - ID do card
- `hub:empresa` - Hub/seção do arquivo
- `sync:jira-md` - Indica que foi sincronizado

## Evitando Duplicatas

O sistema verifica duplicatas de duas formas:
1. Busca por label `card-id:XXX-000`
2. Busca por `[XXX-000]` no título

Cards existentes são atualizados; cards novos são criados.

## Estrutura do Projeto

```
scripts/jira-sync/
├── parser.py         # Extração de YAML dos .md
├── converter.py      # Conversão YAML → Jira API
├── jira_client.py    # Cliente da API REST do Jira
├── sync.py           # CLI principal
├── requirements.txt  # Dependências Python
└── README.md         # Esta documentação
```

## Troubleshooting

### "JIRA_EMAIL não configurado"
Configure as variáveis de ambiente conforme a seção Configuração.

### "Falha na conexão com o Jira"
1. Verifique se o email e token estão corretos
2. Verifique se a URL base está correta
3. Verifique sua conexão com a internet

### "Nenhum card encontrado"
O arquivo deve conter blocos ```yaml com campo "Titulo:" ou "titulo:".

### Erro 400 ao criar issue
Verifique se o tipo de issue (Story, Task, Bug) existe no seu projeto.
