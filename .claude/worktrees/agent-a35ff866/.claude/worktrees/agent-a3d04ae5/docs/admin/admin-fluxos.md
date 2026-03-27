# DOCUMENTACAO DE FLUXOS - MODULO ADMIN (CONFIGURACOES ADMINISTRATIVAS)

> **Versao:** 1.0  
> **Data:** Dezembro 2024  
> **Modulo:** Admin - Configuracoes Administrativas  
> **Objetivo:** Documentacao orientada a fluxos para desenvolvimento

---

## INDICE DE FLUXOS

1. [FLUXO 01: Configuracao de Empresa](#fluxo-01-configuracao-de-empresa)
2. [FLUXO 02: Gestao de Usuarios e Permissoes](#fluxo-02-gestao-de-usuarios-e-permissoes)
3. [FLUXO 03: Integracao com ATS](#fluxo-03-integracao-com-ats)
4. [FLUXO 04: Configuracao de Automacoes](#fluxo-04-configuracao-de-automacoes)
5. [FLUXO 05: Templates de Comunicacao](#fluxo-05-templates-de-comunicacao)
6. [FLUXO 06: Onboarding e Calibracao LIA](#fluxo-06-onboarding-e-calibracao-lia)
7. [FLUXO 07: Configuracao de Beneficios e Cultura](#fluxo-07-configuracao-de-beneficios-e-cultura)
8. [FLUXO 08: Gestao de Perguntas e Testes](#fluxo-08-gestao-de-perguntas-e-testes)

---

## ANALISE DE USO DE IA NO MODULO

### Funcionalidades que USAM IA
| Funcionalidade | Tipo de IA | Modelo | Descricao |
|----------------|------------|--------|-----------|
| Smart Import ATS | NLP/ETL | Claude Sonnet | Mapeamento inteligente de campos entre sistemas |
| Calibracao LIA | Machine Learning | Claude | Ajuste de personalidade e estilo de comunicacao |
| Workflow Suggestions | IA Generativa | Claude | Sugestoes de automacoes baseadas em padroes |
| Template Optimization | NLP | Claude | Sugestoes de melhoria em templates |

### Funcionalidades que PODERIAM usar IA
| Funcionalidade | Sugestao | Beneficio |
|----------------|----------|-----------|
| Config. de Cultura | Analise semantica de textos | Detectar inconsistencias |
| Mapeamento ATS | Auto-match de campos | Reduzir config. manual |
| Analise de Seguranca | Deteccao de anomalias | Alertas proativos |
| Templates | Geracao automatica | Acelerar criacao |

### Funcionalidades OTIMIZAVEIS sem IA
| Funcionalidade | Otimizacao | Impacto |
|----------------|------------|---------|
| Preferencias Usuario | Cache local | -500ms |
| Lista de Integracoes | Lazy loading | -300ms |
| Logs de Sync | Paginacao virtual | Melhor UX |
| Config. Notificacoes | Batch updates | -60% requests |

---

# FLUXO 01: CONFIGURACAO DE EMPRESA

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Configuracao de Dados Institucionais e Estrutura Organizacional**

### O que esse fluxo entrega
Sistema completo para configurar dados institucionais da empresa (CNPJ, endereco, contatos), estrutura organizacional (departamentos, cargos), e preferencias gerais da plataforma.

### Para qual usuario
- Administrador de RH
- Gestor de Recursos Humanos
- Administrador de Sistema

### Resultado final esperado
Empresa configurada com todos os dados institucionais, estrutura organizacional definida, e preferencias de plataforma personalizadas.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Pagina/Componente | Descricao | Arquivo |
|-------------------|-----------|---------|
| SettingsPage | Pagina principal de configuracoes | settings-page.tsx |
| InstitutionalTab | Aba de dados institucionais | settings-page.tsx |
| CultureTab | Aba de cultura organizacional | settings-page.tsx |
| StructureTab | Aba de estrutura organizacional | settings-page.tsx |
| PreferencesTab | Aba de preferencias | settings-page.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/company | GET | Obter dados da empresa |
| /api/v1/company | PUT | Atualizar dados da empresa |
| /api/v1/company/structure | GET | Obter estrutura organizacional |
| /api/v1/company/structure | PUT | Atualizar estrutura |
| /api/v1/company/departments | GET | Listar departamentos |
| /api/v1/company/departments | POST | Criar departamento |
| /api/v1/company/positions | GET | Listar cargos |
| /api/v1/company/positions | POST | Criar cargo |

### Dados

| Tabela | Descricao |
|--------|-----------|
| companies | Dados institucionais da empresa |
| departments | Departamentos da empresa |
| positions | Cargos por departamento |
| company_settings | Configuracoes gerais |
| user_preferences | Preferencias por usuario |

### IA

| Componente | Modelo | Funcao |
|------------|--------|--------|
| N/A | - | Este fluxo nao utiliza IA diretamente |

### Integracoes Externas

| Servico | Uso |
|---------|-----|
| ReceitaWS | Validacao de CNPJ |
| ViaCEP | Busca de endereco por CEP |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| CFG-F01 | Editar Dados Basicos | CNPJ, razao social, nome fantasia |
| CFG-F02 | Configurar Endereco | Endereco completo com busca CEP |
| CFG-F03 | Gerenciar Contatos | Telefones, emails, website |
| CFG-F04 | Configurar Redes Sociais | LinkedIn, Instagram, etc |
| CFG-F05 | Upload Logo | Logo da empresa |
| CFG-F06 | Criar Departamentos | Estrutura departamental |
| CFG-F07 | Criar Cargos | Cargos por departamento |
| CFG-F08 | Definir Hierarquia | Organograma da empresa |
| CFG-F09 | Configurar Tema | Tema claro/escuro/sistema |
| CFG-F10 | Configurar Idioma | Portugues, Ingles, Espanhol |
| CFG-F11 | Configurar Fuso Horario | Timezone da empresa |
| CFG-F12 | Salvar Alteracoes | Persistir configuracoes |
| CFG-F13 | Descartar Alteracoes | Reverter para ultimo salvo |

---

## 4. Documentacao Detalhada (por funcionalidade)

---

### CFG-F01: Editar Dados Basicos

#### Historia de Usuario
"Como administrador de RH, eu quero editar os dados basicos da empresa para manter as informacoes atualizadas na plataforma."

#### Regras de Negocio
1. CNPJ deve ser valido (validacao com ReceitaWS)
2. Razao social e obrigatoria
3. Nome fantasia e opcional
4. Data de fundacao e opcional
5. Setor de atuacao selecionavel de lista

#### Formulas e Logicas
```
Se CNPJ informado:
  Validar formato (14 digitos)
  Consultar ReceitaWS
  Se valido: preencher campos automaticamente
  Se invalido: exibir erro

Validacao CNPJ:
  - Remover pontuacao
  - Validar digitos verificadores
  - Verificar se nao e sequencia invalida
```

#### Inputs
- CNPJ (string, 14 digitos)
- Razao Social (string, obrigatorio)
- Nome Fantasia (string, opcional)
- Data Fundacao (date, opcional)
- Setor (enum)

#### Outputs
- company_id (uuid)
- updated_at (timestamp)
- status (success/error)

#### Validacoes
- CNPJ formato valido
- Razao social nao vazia (min 3 chars)
- Nome fantasia max 100 chars

#### Edge Cases
- CNPJ invalido: exibir erro e nao permitir salvar
- ReceitaWS offline: permitir salvar sem validacao online
- Empresa ja cadastrada: atualizar dados existentes

---

### CFG-F02: Configurar Endereco

#### Historia de Usuario
"Como administrador, eu quero configurar o endereco da empresa com busca automatica por CEP para facilitar o preenchimento."

#### Regras de Negocio
1. CEP com busca automatica (ViaCEP)
2. Campos preenchidos automaticamente ao digitar CEP
3. Usuario pode editar campos apos busca
4. Numero e obrigatorio se logradouro informado
5. Complemento e opcional

#### Formulas e Logicas
```
Ao digitar CEP (8 digitos):
  Chamar ViaCEP: https://viacep.com.br/ws/{cep}/json/
  Se encontrado:
    Preencher: logradouro, bairro, cidade, estado
    Focar no campo "numero"
  Se nao encontrado:
    Exibir aviso: "CEP nao encontrado"
    Permitir preenchimento manual
```

#### Inputs
- CEP (string, 8 digitos)
- Logradouro (string)
- Numero (string)
- Complemento (string)
- Bairro (string)
- Cidade (string)
- Estado (string, 2 chars)

#### Outputs
- Endereco completo persistido
- Geolocalizacao (lat, lng) opcional

#### Validacoes
- CEP formato valido
- Estado valido (siglas BR)
- Numero obrigatorio se logradouro informado

#### Edge Cases
- CEP inexistente: permitir preenchimento manual
- ViaCEP timeout: fallback para preenchimento manual
- Endereco internacional: permitir texto livre

---

### CFG-F06: Criar Departamentos

#### Historia de Usuario
"Como administrador de RH, eu quero criar departamentos para organizar a estrutura da empresa."

#### Regras de Negocio
1. Nome do departamento obrigatorio
2. Nome unico na empresa
3. Departamento pai opcional (hierarquia)
4. Responsavel pelo departamento opcional
5. Limite de 100 departamentos por empresa

#### Formulas e Logicas
```
Validacao nome:
  Se nome existe em departments WHERE company_id = current:
    Erro: "Departamento ja existe"
    
Hierarquia:
  Max 5 niveis de profundidade
  Nao permitir ciclos
```

#### Inputs
```json
{
  "name": "Tecnologia",
  "parent_id": null,
  "manager_id": "uuid-do-gestor",
  "description": "Departamento de TI"
}
```

#### Outputs
```json
{
  "id": "uuid",
  "name": "Tecnologia",
  "parent_id": null,
  "manager": {...},
  "positions_count": 0,
  "employees_count": 0,
  "created_at": "2024-12-01T10:00:00Z"
}
```

#### Validacoes
- Nome nao vazio (3-50 chars)
- Nome unico por empresa
- Parent valido (se informado)
- Sem ciclos na hierarquia

#### Edge Cases
- Nome duplicado: erro 409 Conflict
- Limite excedido: erro 403 + upgrade plan message
- Parent inexistente: erro 404

---

## 5. Cards de Especificacao (Estilo Jira)

---

### CARD CFG-FLOW-001: Configuracao Completa de Empresa

```yaml
Titulo: [FULL-STACK] Implementar Configuracao de Empresa
Tipo: Epic
Sprint: 1-2
Pontos: 34

Descricao: |
  Implementar sistema completo de configuracao da empresa,
  incluindo dados institucionais, endereco, e contatos.

Historia de Usuario: |
  Como administrador de RH, eu quero configurar os dados
  da minha empresa para personalizar a plataforma.

Regras de Negocio:
  1. CNPJ validado via ReceitaWS
  2. CEP com busca ViaCEP
  3. Logo com upload de imagem
  4. Redes sociais com validacao de URL
  5. Persistencia automatica com debounce

Requisitos Tecnicos:
  Frontend:
    - InstitutionalTab component
    - Form com validacao em tempo real
    - Upload de imagem com crop
    - Busca CEP automatica
  Backend:
    - PUT /api/v1/company
    - Integracao ReceitaWS
    - Integracao ViaCEP
    - Storage para logo
  Dados:
    - companies (CNPJ, razao_social, endereco, etc)
    - company_settings (preferencias)

Integracoes:
  - ReceitaWS (CNPJ)
  - ViaCEP (endereco)
  - S3/Storage (logo)

Riscos:
  - ReceitaWS instavel: cache + fallback
  - Upload de imagem grande: limite 5MB + compressao

DoD:
  - [ ] Dados basicos salvam
  - [ ] CNPJ validado
  - [ ] CEP busca automatica
  - [ ] Logo upload funciona
  - [ ] Redes sociais validadas
  - [ ] Testes unitarios passando

Criterios de Aceitacao:
  - [ ] Editar CNPJ valida e preenche dados
  - [ ] Digitar CEP preenche endereco
  - [ ] Upload logo exibe preview
  - [ ] Salvar persiste todas alteracoes
```

---

### CARD CFG-FLOW-002: Estrutura Organizacional

```yaml
Titulo: [FULL-STACK] Implementar Estrutura Organizacional
Tipo: Feature
Sprint: 2
Pontos: 21

Descricao: |
  Sistema de departamentos e cargos com hierarquia visual.

Historia de Usuario: |
  Como administrador, eu quero definir a estrutura da empresa
  com departamentos e cargos para organizar o recrutamento.

Regras de Negocio:
  1. Departamentos com hierarquia (max 5 niveis)
  2. Cargos vinculados a departamentos
  3. Organograma visual
  4. Responsavel por departamento
  5. Limite de 100 departamentos

Requisitos Tecnicos:
  Frontend:
    - StructureTab component
    - Tree view para hierarquia
    - Drag-drop para reordenar
    - Modal de criacao/edicao
  Backend:
    - CRUD /api/v1/company/departments
    - CRUD /api/v1/company/positions
    - Validacao de hierarquia
  Dados:
    - departments (name, parent_id, manager_id)
    - positions (name, department_id, level)

DoD:
  - [ ] CRUD departamentos funciona
  - [ ] CRUD cargos funciona
  - [ ] Hierarquia exibe corretamente
  - [ ] Drag-drop funciona
  - [ ] Limite validado

Criterios de Aceitacao:
  - [ ] Criar "Tecnologia" com subdepartamento "Backend"
  - [ ] Criar cargo "Dev Senior" em Tecnologia
  - [ ] Arrastar departamento reorganiza
```

---

## 6. Diagrama da Jornada do Fluxo

### Jornada do Usuario

```
INICIO
  |
  v
[Admin acessa Configuracoes]
  |
  v
[Sidebar com categorias de config]
  |
  v
[Clica em "Dados da Empresa"]
  |
  v
[Form com dados atuais carregados]
  |
  v
[Edita CNPJ]
  |
  +-- Sistema valida formato
  |
  v
[Sistema busca dados ReceitaWS]
  |
  v
[Campos preenchidos automaticamente]
  |
  +-- Razao Social, Nome Fantasia
  |
  v
[Usuario digita CEP]
  |
  v
[Sistema busca ViaCEP]
  |
  v
[Endereco preenchido automaticamente]
  |
  v
[Usuario faz upload de logo]
  |
  v
[Preview exibido com crop]
  |
  v
[Usuario confirma alteracoes]
  |
  v
[Clica em "Salvar Alteracoes"]
  |
  v
[Loading durante save]
  |
  v
[Toast: "Configuracoes salvas com sucesso"]
  |
FIM
```

### Jornada do Sistema

```
[FRONT] Admin clica em "Dados da Empresa"
    |
    v
[FRONT] Renderiza InstitutionalTab
    |
    v
[BACK] GET /api/v1/company
    |
    v
[DADOS] SELECT * FROM companies WHERE id = company_id
    |
    v
[BACK] Retorna dados da empresa
    |
    v
[FRONT] Preenche formulario com dados
    |
    v
[FRONT] Usuario edita CNPJ
    |
    v
[FRONT] Debounce 500ms
    |
    v
[FRONT] Chama ReceitaWS API
    |
    v
[EXT] ReceitaWS retorna dados do CNPJ
    |
    v
[FRONT] Preenche campos automaticamente
    |
    v
[FRONT] Usuario digita CEP
    |
    v
[EXT] ViaCEP retorna endereco
    |
    v
[FRONT] Preenche campos de endereco
    |
    v
[FRONT] Usuario clica Salvar
    |
    v
[BACK] PUT /api/v1/company
    |
    v
[DADOS] UPDATE companies SET ... WHERE id = company_id
    |
    v
[BACK] Retorna success
    |
    v
[FRONT] Toast de sucesso
    |
FIM
```

---

## 7. Roadmap do Fluxo em Fases

### Fase 1: MVP Configuracao (Sprint 1)
```
[Dados basicos da empresa]
         |
         v
[Endereco com busca CEP]
         |
         v
[Upload de logo]
         |
         v
[Salvar/Descartar alteracoes]

Dependencias: Nenhuma
Entregaveis:
  - Form de dados basicos
  - Integracao ViaCEP
  - Upload de imagem
  - Persistencia
```

### Fase 2: Estrutura Organizacional (Sprint 2)
```
[CRUD Departamentos]
         |
         v
[CRUD Cargos]
         |
         v
[Visualizacao hierarquica]
         |
         v
[Drag-drop reorganizacao]

Dependencias: Fase 1 completa
Entregaveis:
  - Gestao de departamentos
  - Gestao de cargos
  - Organograma visual
```

### Fase 3: Validacoes Avancadas (Sprint 3)
```
[Integracao ReceitaWS]
         |
         v
[Validacao de redes sociais]
         |
         v
[Geolocalizacao de endereco]

Dependencias: Fase 2 completa
Entregaveis:
  - Validacao CNPJ online
  - URLs validadas
  - Mapa de localizacao
```

---

## 8. Lista de Tasks Importaveis

```csv
ID,Titulo,Descricao,Tipo,Dependencias,DoD,Est Ideal,Est Real,Est Pess
CFG-F01-T1,[FRONT] Form Dados Basicos,Formulario de dados institucionais,feature,,Form renderiza com validacao,4h,6h,10h
CFG-F01-T2,[BACK] API Company CRUD,Endpoints GET/PUT company,feature,,API funciona,4h,6h,10h
CFG-F02-T1,[FRONT] Integracao ViaCEP,Busca automatica de CEP,feature,CFG-F01-T1,CEP busca e preenche,2h,3h,5h
CFG-F02-T2,[BACK] Integracao ReceitaWS,Validacao de CNPJ,feature,,CNPJ validado,3h,5h,8h
CFG-F05-T1,[FRONT] Upload Logo,Upload com preview e crop,feature,,Upload funciona,4h,6h,10h
CFG-F05-T2,[BACK] Storage Logo,API de upload para S3/Storage,feature,,Arquivo salvo,3h,5h,8h
CFG-F06-T1,[BACK] CRUD Departamentos,Endpoints de departamentos,feature,,CRUD funciona,4h,6h,10h
CFG-F06-T2,[FRONT] Tree Departamentos,Componente de arvore hierarquica,feature,CFG-F06-T1,Arvore renderiza,5h,8h,12h
CFG-F07-T1,[BACK] CRUD Cargos,Endpoints de cargos,feature,CFG-F06-T1,CRUD funciona,3h,5h,8h
CFG-F07-T2,[FRONT] Lista Cargos,Componente de lista de cargos,feature,CFG-F07-T1,Lista renderiza,3h,5h,8h
CFG-F08-T1,[FRONT] Organograma Visual,Visualizacao de hierarquia,feature,CFG-F06-T2,Organograma exibe,6h,10h,16h
CFG-F12-T1,[FRONT] Save/Discard Bar,Barra de acoes com hasChanges,feature,,Barra funciona,2h,3h,5h
CFG-F13-T1,[FRONT] Confirm Discard,Dialog de confirmacao,feature,CFG-F12-T1,Dialog funciona,1h,2h,3h
```

---

## 9. Padrao de Design do Fluxo

### Componentes Necessarios

| Componente | Framework | Funcao |
|------------|-----------|--------|
| Card | shadcn/ui | Container de secoes |
| Input | shadcn/ui | Campos de texto |
| Select | shadcn/ui | Dropdowns |
| Button | shadcn/ui | Acoes |
| Avatar | shadcn/ui | Logo preview |
| Tree | custom | Hierarquia departamentos |
| Dialog | shadcn/ui | Modais de confirmacao |
| Toast | shadcn/ui | Feedback de acoes |

### Paleta de Cores

```css
/* Cores principais */
--color-primary: #60BED1;      /* Accent - acoes principais */
--color-bg-card: #FFFFFF;       /* Fundo de cards */
--color-bg-page: #F9FAFB;       /* Fundo da pagina */
--color-border: #E5E7EB;        /* Bordas (gray-200) */

/* Texto */
--color-text-primary: #111827;   /* Titulos (gray-900) */
--color-text-secondary: #4B5563; /* Corpo (gray-600) */
--color-text-muted: #9CA3AF;     /* Hints (gray-400) */

/* Status */
--color-success: #10B981;
--color-warning: #F59E0B;
--color-error: #EF4444;
```

### Tokens de Tipografia

```css
/* Titulos - Source Serif 4 */
.title-xl { font: 600 18px/26px 'Source Serif 4'; }
.title { font: 600 14px/20px 'Source Serif 4'; }

/* Corpo - Open Sans */
.body { font: 400 14px/20px 'Open Sans'; }
.body-small { font: 400 12px/16px 'Open Sans'; }
.caption { font: 400 11px/14px 'Open Sans'; }
```

---

## 10. Uso de IA no Fluxo

**Este fluxo NAO utiliza IA diretamente.**

### Possibilidades de Expansao com IA

| Feature | Tipo IA | Beneficio |
|---------|---------|-----------|
| Sugestao de estrutura | Claude | Sugerir departamentos com base no setor |
| Validacao de cultura | NLP | Detectar inconsistencias nos textos |
| Auto-complete cargos | Claude | Sugerir cargos baseado no departamento |

---

# FLUXO 02: GESTAO DE USUARIOS E PERMISSOES

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Gestao de Usuarios, Roles e Permissoes**

### O que esse fluxo entrega
Sistema de gerenciamento de usuarios da plataforma com roles pre-definidos, permissoes granulares, e controle de acesso.

### Para qual usuario
- Administrador de Sistema
- Gestor de RH (visualizacao)

### Resultado final esperado
Usuarios cadastrados com roles apropriados e permissoes configuradas para cada modulo da plataforma.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| SecurityTab | Aba de seguranca |
| UsersTable | Tabela de usuarios |
| UserInviteModal | Modal de convite |
| RolesManager | Gerenciador de roles |
| PermissionsMatrix | Matriz de permissoes |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/users | GET | Listar usuarios |
| /api/v1/users | POST | Criar usuario |
| /api/v1/users/{id} | PUT | Editar usuario |
| /api/v1/users/{id} | DELETE | Remover usuario |
| /api/v1/roles | GET | Listar roles |
| /api/v1/roles | POST | Criar role |
| /api/v1/permissions | GET | Listar permissoes |
| /api/v1/users/invite | POST | Enviar convite |

### Dados

| Tabela | Campos |
|--------|--------|
| users | id, email, name, role_id, status, last_login |
| roles | id, name, description, permissions |
| permissions | id, module, action, description |
| user_invites | id, email, role_id, token, expires_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| USR-F01 | Listar Usuarios | Ver todos usuarios da empresa |
| USR-F02 | Convidar Usuario | Enviar email de convite |
| USR-F03 | Editar Usuario | Alterar dados e role |
| USR-F04 | Desativar Usuario | Suspender acesso |
| USR-F05 | Reativar Usuario | Restaurar acesso |
| USR-F06 | Excluir Usuario | Remover permanentemente |
| USR-F07 | Buscar Usuarios | Filtrar por nome/email |
| USR-F08 | Filtrar por Role | Filtrar por cargo |
| USR-F09 | Listar Roles | Ver roles disponiveis |
| USR-F10 | Criar Role Custom | Role personalizado |
| USR-F11 | Editar Role | Alterar permissoes |
| USR-F12 | Ver Matriz Permissoes | Visao geral de acessos |

---

## 4. Documentacao Detalhada

### USR-F02: Convidar Usuario

#### Historia de Usuario
"Como administrador, eu quero convidar novos usuarios para a plataforma por email."

#### Regras de Negocio
1. Email deve ser unico na empresa
2. Role obrigatorio
3. Convite expira em 7 dias
4. Limite de usuarios por plano
5. Email de convite com link de ativacao

#### Formulas e Logicas
```
Ao enviar convite:
  1. Verificar email nao existe em users
  2. Verificar limite de usuarios do plano
  3. Gerar token unico (UUID v4)
  4. Salvar em user_invites
  5. Enviar email com link: /activate?token={token}
  6. Token expira em 7 dias
```

#### Inputs
```json
{
  "email": "novo.usuario@empresa.com",
  "name": "Novo Usuario",
  "role_id": "uuid-do-role",
  "send_email": true
}
```

#### Outputs
```json
{
  "invite_id": "uuid",
  "email": "novo.usuario@empresa.com",
  "expires_at": "2024-12-08T10:00:00Z",
  "activation_link": "https://..."
}
```

#### Edge Cases
- Email ja cadastrado: erro 409
- Limite de usuarios: erro 403 + upsell
- Email invalido: erro 400
- Reenviar convite: atualizar token e expiracao

---

## 5. Cards de Especificacao

### CARD USR-FLOW-001: Gestao Completa de Usuarios

```yaml
Titulo: [FULL-STACK] Implementar Gestao de Usuarios
Tipo: Epic
Sprint: 2-3
Pontos: 34

Descricao: |
  Sistema completo de usuarios com convite, edicao,
  desativacao e gestao de roles.

Requisitos Tecnicos:
  Frontend:
    - UsersTable com paginacao
    - UserInviteModal
    - UserEditModal
    - RoleSelector
    - StatusBadge
  Backend:
    - CRUD /api/v1/users
    - Envio de email de convite
    - Validacao de limite do plano
  Dados:
    - users, roles, permissions

DoD:
  - [ ] Convidar usuario funciona
  - [ ] Email de convite enviado
  - [ ] Editar usuario funciona
  - [ ] Desativar/reativar funciona
  - [ ] Roles selecionaveis
```

---

## 6. Diagrama da Jornada do Fluxo

```
INICIO
  |
  v
[Admin acessa Seguranca > Usuarios]
  |
  v
[Tabela de usuarios carrega]
  |
  v
[Clica em "Convidar Usuario"]
  |
  v
[Modal de convite abre]
  |
  v
[Preenche email e seleciona role]
  |
  v
[Clica em "Enviar Convite"]
  |
  v
[BACK] Valida email e limite
  |
  v
[BACK] Cria invite e envia email
  |
  v
[Toast: "Convite enviado para email@empresa.com"]
  |
  v
[Usuario aparece como "Pendente"]
  |
  v
[Usuario recebe email e clica no link]
  |
  v
[Pagina de ativacao]
  |
  v
[Usuario define senha]
  |
  v
[Usuario ativado e pronto para usar]
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: CRUD Usuarios (Sprint 2)
- Listar usuarios
- Convidar usuario
- Ativacao de conta

### Fase 2: Roles e Permissoes (Sprint 3)
- Roles pre-definidos
- Roles customizados
- Matriz de permissoes

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
USR-F01-T1,[BACK] API Listar Usuarios,feature,3h
USR-F01-T2,[FRONT] UsersTable,feature,5h
USR-F02-T1,[BACK] API Invite,feature,4h
USR-F02-T2,[BACK] Email Service,feature,4h
USR-F02-T3,[FRONT] InviteModal,feature,4h
USR-F03-T1,[BACK] API Edit User,feature,3h
USR-F03-T2,[FRONT] EditModal,feature,4h
USR-F04-T1,[BACK] API Deactivate,feature,2h
USR-F09-T1,[BACK] API Roles,feature,3h
USR-F10-T1,[FRONT] RoleManager,feature,5h
```

---

## 9. Padrao de Design

### Componentes
- DataTable para lista de usuarios
- Badge para status (ativo, pendente, inativo)
- Avatar com iniciais
- Dropdown para acoes

---

## 10. Uso de IA no Fluxo

**Este fluxo NAO utiliza IA diretamente.**

---

# FLUXO 03: INTEGRACAO COM ATS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Integracao com Sistemas ATS Externos**

### O que esse fluxo entrega
Sistema de integracao bidirecional com sistemas ATS (SAP SuccessFactors, Workday, BambooHR, Greenhouse), incluindo mapeamento de campos, sincronizacao automatica, e logs de operacoes.

### Para qual usuario
- Administrador de Sistema
- Administrador de RH

### Resultado final esperado
Dados de candidatos e vagas sincronizados automaticamente entre a Plataforma LIA e sistemas ATS externos.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao | Arquivo |
|------------|-----------|---------|
| ATSIntegrationsPage | Pagina de integracoes ATS | ats-integrations-page.tsx |
| SystemCard | Card de sistema ATS | ats-integrations-page.tsx |
| FieldMappingModal | Modal de mapeamento | ats-integrations-page.tsx |
| SyncLogsTable | Tabela de logs de sync | ats-integrations-page.tsx |
| ConnectionWizard | Wizard de conexao | ats-integrations-page.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/integrations/ats | GET | Listar sistemas ATS |
| /api/v1/integrations/ats/{id} | POST | Conectar sistema |
| /api/v1/integrations/ats/{id} | DELETE | Desconectar |
| /api/v1/integrations/ats/{id}/sync | POST | Sincronizar |
| /api/v1/integrations/ats/{id}/mapping | GET | Ver mapeamento |
| /api/v1/integrations/ats/{id}/mapping | PUT | Atualizar mapeamento |
| /api/v1/integrations/ats/{id}/logs | GET | Logs de sync |

### Dados

| Tabela | Campos |
|--------|--------|
| ats_integrations | id, company_id, type, status, config |
| ats_field_mappings | integration_id, source_field, target_field, active |
| ats_sync_logs | integration_id, type, status, records, duration |

### IA

| Componente | Modelo | Funcao |
|------------|--------|--------|
| Smart Field Mapping | Claude Sonnet | Sugerir mapeamento automatico de campos |

### Integracoes Externas

| Servico | Uso |
|---------|-----|
| SAP SuccessFactors API | Candidatos, Vagas, Entrevistas |
| Workday HCM API | Funcionarios, Requisicoes |
| BambooHR API | Colaboradores, Relatorios |
| Greenhouse API | Candidatos, Vagas, Scorecards |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| ATS-F01 | Listar Sistemas | Ver ATS disponiveis |
| ATS-F02 | Conectar Sistema | Wizard de conexao OAuth/API |
| ATS-F03 | Testar Conexao | Verificar credenciais |
| ATS-F04 | Configurar Webhook | URL de callback |
| ATS-F05 | Mapear Campos | De-para de campos |
| ATS-F06 | Smart Mapping LIA | Sugestao automatica de mapeamento |
| ATS-F07 | Sincronizar Manual | Trigger de sync imediato |
| ATS-F08 | Agendar Sync | Frequencia automatica |
| ATS-F09 | Ver Logs | Historico de sincronizacoes |
| ATS-F10 | Resolver Erros | Tratamento de falhas |
| ATS-F11 | Pausar Integracao | Suspender sync |
| ATS-F12 | Desconectar | Remover integracao |

---

## 4. Documentacao Detalhada

### ATS-F06: Smart Mapping LIA

#### Historia de Usuario
"Como administrador, eu quero que a LIA sugira o mapeamento de campos automaticamente para acelerar a configuracao."

#### Regras de Negocio
1. Analisar campos de origem e destino
2. Usar semantica para sugerir correspondencias
3. Exibir nivel de confianca (0-100%)
4. Permitir ajustes manuais
5. Aprender com correcoes do usuario

#### Formulas e Logicas
```
PROMPT Claude:
"Analise os campos de origem e destino e sugira mapeamentos.
Campos origem (SAP): {source_fields}
Campos destino (LIA): {target_fields}

Para cada campo de origem, sugira:
- target_field: campo destino correspondente
- confidence: nivel de confianca (0-1)
- reasoning: explicacao da escolha

Retorne JSON."

Logica de matching:
  confidence >= 0.9: match automatico (verde)
  confidence >= 0.7: sugestao forte (amarelo)
  confidence >= 0.5: sugestao fraca (laranja)
  confidence < 0.5: nao sugerir
```

#### Inputs
```json
{
  "source_fields": [
    {"name": "candidateName", "type": "string"},
    {"name": "emailAddress", "type": "email"},
    {"name": "yearsExperience", "type": "number"}
  ],
  "target_fields": [
    {"name": "name", "type": "string"},
    {"name": "email", "type": "email"},
    {"name": "experience_years", "type": "number"}
  ]
}
```

#### Outputs
```json
{
  "mappings": [
    {
      "source": "candidateName",
      "target": "name",
      "confidence": 0.95,
      "reasoning": "Nome semanticamente equivalente"
    },
    {
      "source": "emailAddress",
      "target": "email",
      "confidence": 0.98,
      "reasoning": "Campo de email correspondente"
    }
  ],
  "unmapped_source": [],
  "unmapped_target": ["phone"]
}
```

#### Edge Cases
- Campos sem correspondencia: listar para mapeamento manual
- Multiplas opcoes: exibir todas com ranking
- Tipos incompativeis: alertar usuario

---

## 5. Cards de Especificacao

### CARD ATS-FLOW-001: Integracao Completa SAP SuccessFactors

```yaml
Titulo: [FULL-STACK] Implementar Integracao SAP SuccessFactors
Tipo: Epic
Sprint: 3-4
Pontos: 55

Descricao: |
  Integracao completa com SAP SuccessFactors para sincronizacao
  bidirecional de candidatos, vagas e entrevistas.

Historia de Usuario: |
  Como administrador de RH, eu quero conectar meu SAP SuccessFactors
  para sincronizar candidatos automaticamente com a Plataforma LIA.

Regras de Negocio:
  1. OAuth 2.0 para autenticacao
  2. Mapeamento de campos configuravel
  3. Sync bidirecional (import/export)
  4. Webhook para eventos em tempo real
  5. Logs detalhados de cada operacao
  6. Retry automatico em caso de falha

Requisitos Tecnicos:
  Frontend:
    - ConnectionWizard (3 steps)
    - FieldMappingEditor
    - SyncLogsTable com filtros
    - StatusBadge em tempo real
  Backend:
    - OAuth flow com SAP
    - Worker de sincronizacao
    - Fila de jobs (Bull/Redis)
    - Webhook receiver
  Dados:
    - ats_integrations
    - ats_field_mappings
    - ats_sync_logs
  IA:
    - Smart Mapping com Claude

Integracoes:
  - SAP SuccessFactors OData API
  - Redis (fila de jobs)

Riscos:
  - API SAP instavel: retry + exponential backoff
  - Rate limiting: respeitar limites da API
  - Dados grandes: paginacao + batch processing

DoD:
  - [ ] OAuth funciona
  - [ ] Mapeamento de campos funciona
  - [ ] Sync importa candidatos
  - [ ] Webhook recebe eventos
  - [ ] Logs exibem historico
  - [ ] Erros sao tratados

Criterios de Aceitacao:
  - [ ] Conectar SAP com credenciais validas
  - [ ] Smart Mapping sugere correspondencias
  - [ ] Sync importa 100+ candidatos
  - [ ] Novo candidato via webhook aparece em <1min
```

---

## 6. Diagrama da Jornada do Fluxo

### Conectar Novo Sistema ATS

```
INICIO
  |
  v
[Admin acessa Integracoes > ATS]
  |
  v
[Cards de sistemas disponiveis]
  |
  +-- SAP (desconectado)
  +-- Workday (desconectado)
  +-- BambooHR (desconectado)
  |
  v
[Clica em "Conectar" no SAP]
  |
  v
[ConnectionWizard Step 1: Credenciais]
  |
  v
[Preenche API Key e Secret]
  |
  v
[Clica em "Testar Conexao"]
  |
  v
[BACK] Valida credenciais com SAP API
  |
  v
[Sucesso: avanca para Step 2]
  |
  v
[Step 2: Mapeamento de Campos]
  |
  v
[Clica em "Smart Mapping LIA"]
  |
  v
[IA] Claude analisa campos e sugere
  |
  v
[Exibe sugestoes com confidence]
  |
  v
[Usuario confirma/ajusta mapeamentos]
  |
  v
[Step 3: Configurar Sync]
  |
  v
[Seleciona frequencia: Hourly]
  |
  v
[Configura webhook URL]
  |
  v
[Clica em "Ativar Integracao"]
  |
  v
[BACK] Salva config e inicia primeira sync
  |
  v
[Card SAP agora mostra "Conectado"]
  |
  v
[Primeira sync em background]
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: SAP SuccessFactors (Sprint 3)
- Conexao OAuth
- Mapeamento basico
- Sync de candidatos

### Fase 2: Smart Mapping (Sprint 3)
- Integracao Claude para sugestoes
- UI de mapeamento visual

### Fase 3: Outros ATS (Sprint 4)
- Workday HCM
- BambooHR
- Greenhouse

### Fase 4: Bidirecional (Sprint 5)
- Export de dados para ATS
- Webhooks bidirecionais

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
ATS-F01-T1,[FRONT] SystemCards Grid,feature,4h
ATS-F02-T1,[FRONT] ConnectionWizard,feature,8h
ATS-F02-T2,[BACK] OAuth SAP,feature,8h
ATS-F03-T1,[BACK] Test Connection API,feature,3h
ATS-F05-T1,[FRONT] FieldMappingEditor,feature,8h
ATS-F05-T2,[BACK] CRUD Mappings API,feature,4h
ATS-F06-T1,[IA] Smart Mapping Prompt,feature,4h
ATS-F06-T2,[BACK] Claude Integration,feature,6h
ATS-F07-T1,[BACK] Sync Worker,feature,10h
ATS-F08-T1,[BACK] Scheduler Service,feature,6h
ATS-F09-T1,[FRONT] SyncLogsTable,feature,5h
ATS-F09-T2,[BACK] Logs API,feature,3h
```

---

## 9. Padrao de Design

### Componentes
- Card para cada sistema ATS
- Badge de status (conectado, conectando, erro)
- Wizard de 3 steps
- Drag-drop para mapeamento visual
- Tabela de logs com filtros

---

## 10. Uso de IA no Fluxo

**Este fluxo UTILIZA IA para Smart Field Mapping.**

### Detalhes da Implementacao IA

| Aspecto | Especificacao |
|---------|---------------|
| Modelo | Claude Sonnet |
| Prompt | Analise semantica de campos |
| Input | Arrays de campos origem/destino |
| Output | JSON com mapeamentos + confianca |
| Fallback | Mapeamento manual |
| Timeout | 10 segundos |

### Prompt Template
```
Voce e um especialista em integracao de sistemas de RH.
Analise os campos abaixo e sugira o melhor mapeamento.

Campos do sistema origem ({source_system}):
{source_fields_json}

Campos do sistema destino (Plataforma LIA):
{target_fields_json}

Retorne um JSON com:
- mappings: array de {source, target, confidence, reasoning}
- unmapped_source: campos origem sem correspondencia
- unmapped_target: campos destino sem correspondencia
```

---

# FLUXO 04: CONFIGURACAO DE AUTOMACOES

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Workflow Builder - Automacoes Inteligentes**

### O que esse fluxo entrega
Sistema visual de criacao de workflows automatizados com triggers, condicoes, acoes e delays. Permite automatizar processos de recrutamento como onboarding, lembretes e follow-ups.

### Para qual usuario
- Administrador de RH
- Gestor de Recrutamento

### Resultado final esperado
Workflows automatizados executando acoes baseadas em triggers e condicoes configuradas.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao | Arquivo |
|------------|-----------|---------|
| WorkflowAutomationPage | Pagina principal | workflow-automation-page.tsx |
| WorkflowCanvas | Canvas drag-drop | workflow-automation-page.tsx |
| NodePalette | Paleta de componentes | workflow-automation-page.tsx |
| WorkflowCard | Card de workflow | workflow-automation-page.tsx |
| TemplateGrid | Grid de templates | workflow-automation-page.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/workflows | GET | Listar workflows |
| /api/v1/workflows | POST | Criar workflow |
| /api/v1/workflows/{id} | PUT | Editar workflow |
| /api/v1/workflows/{id} | DELETE | Excluir |
| /api/v1/workflows/{id}/activate | POST | Ativar |
| /api/v1/workflows/{id}/deactivate | POST | Desativar |
| /api/v1/workflows/{id}/test | POST | Testar |
| /api/v1/workflows/templates | GET | Templates prontos |

### Dados

| Tabela | Campos |
|--------|--------|
| workflows | id, name, trigger, nodes, edges, status |
| workflow_executions | workflow_id, started_at, status, context |
| workflow_templates | id, name, category, workflow_json |

### IA

| Componente | Modelo | Funcao |
|------------|--------|--------|
| Workflow Suggestions | Claude | Sugerir automacoes baseado em padroes |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| WFL-F01 | Listar Workflows | Ver workflows criados |
| WFL-F02 | Criar Workflow | Novo workflow do zero |
| WFL-F03 | Usar Template | Criar a partir de template |
| WFL-F04 | Adicionar Trigger | Definir evento de disparo |
| WFL-F05 | Adicionar Condicao | Logica condicional (if/else) |
| WFL-F06 | Adicionar Acao | Email, WhatsApp, tarefa |
| WFL-F07 | Adicionar Delay | Espera temporal |
| WFL-F08 | Conectar Nodes | Definir fluxo |
| WFL-F09 | Testar Workflow | Simulacao |
| WFL-F10 | Ativar Workflow | Habilitar execucao |
| WFL-F11 | Desativar Workflow | Pausar execucao |
| WFL-F12 | Ver Execucoes | Historico de runs |
| WFL-F13 | Ver Analytics | Metricas de performance |

---

## 4. Documentacao Detalhada

### WFL-F04: Adicionar Trigger

#### Historia de Usuario
"Como gestor de RH, eu quero definir quando meu workflow deve ser disparado."

#### Regras de Negocio
1. Todo workflow deve ter exatamente 1 trigger
2. Triggers disponiveis:
   - candidate_approved: Candidato aprovado
   - interview_scheduled: Entrevista agendada
   - document_uploaded: Documento enviado
   - feedback_received: Feedback recebido
3. Trigger e o primeiro node do fluxo
4. Pode ter filtros condicionais

#### Inputs
```json
{
  "type": "trigger",
  "event": "candidate_approved",
  "filters": {
    "department": ["Tecnologia", "Produto"]
  }
}
```

#### Outputs
- Node criado no canvas
- Conexao disponivel para proximo node

---

### WFL-F06: Adicionar Acao

#### Historia de Usuario
"Como gestor, eu quero definir acoes automaticas como envio de email."

#### Regras de Negocio
1. Acoes disponiveis:
   - send_email: Enviar email
   - send_whatsapp: Enviar WhatsApp
   - send_sms: Enviar SMS
   - update_status: Atualizar status
   - create_task: Criar tarefa
   - schedule_meeting: Agendar reuniao
2. Cada acao tem config especifica
3. Templates de mensagem disponiveis

#### Formulas e Logicas
```
Para send_email:
  - template_id: template de email
  - recipients: candidato | gestor | custom
  - variables: {candidate_name}, {job_title}, etc
  
Para update_status:
  - target_status: novo status
  - notify: enviar notificacao?
```

---

## 5. Cards de Especificacao

### CARD WFL-FLOW-001: Workflow Builder Visual

```yaml
Titulo: [FULL-STACK] Implementar Workflow Builder Visual
Tipo: Epic
Sprint: 4-5
Pontos: 55

Descricao: |
  Sistema visual de criacao de workflows com drag-drop,
  conexoes entre nodes e execucao automatizada.

Requisitos Tecnicos:
  Frontend:
    - Canvas com React Flow ou custom
    - Paleta de componentes drag-drop
    - Configuracao de nodes inline
    - Preview de execucao
  Backend:
    - Engine de execucao de workflows
    - Scheduler para delays
    - Integracao com servicos de notificacao
  Dados:
    - workflows (nodes, edges como JSON)
    - workflow_executions

DoD:
  - [ ] Canvas drag-drop funciona
  - [ ] Todos tipos de nodes funcionam
  - [ ] Conexoes entre nodes funcionam
  - [ ] Execucao de teste funciona
  - [ ] Execucao real funciona
```

---

## 6. Diagrama da Jornada do Fluxo

```
INICIO
  |
  v
[Gestor acessa Automacoes]
  |
  v
[Clica em "Novo Workflow"]
  |
  v
[Seleciona: Do zero ou Template]
  |
  v
[Canvas em branco abre]
  |
  v
[Arrasta Trigger "Candidato Aprovado"]
  |
  v
[Configura filtro: Departamento = TI]
  |
  v
[Arrasta Condicao "Verificar Cargo"]
  |
  v
[Conecta Trigger -> Condicao]
  |
  v
[Arrasta Acao "Enviar Email"]
  |
  v
[Seleciona template "Welcome Kit TI"]
  |
  v
[Conecta Condicao (true) -> Email]
  |
  v
[Arrasta outra Acao "Criar Tarefa"]
  |
  v
[Conecta Condicao (false) -> Tarefa]
  |
  v
[Clica em "Testar"]
  |
  v
[Simula execucao com dados de teste]
  |
  v
[Resultado: OK]
  |
  v
[Clica em "Ativar Workflow"]
  |
  v
[Workflow ativo e monitorando]
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: Canvas Basico (Sprint 4)
- Drag-drop de nodes
- Conexoes visuais
- Tipos basicos: trigger, action

### Fase 2: Logica Avancada (Sprint 4)
- Condicoes (if/else)
- Delays
- Loops

### Fase 3: Execucao (Sprint 5)
- Engine de execucao
- Logs de execucao
- Retry em falhas

### Fase 4: Analytics (Sprint 5)
- Metricas de performance
- Taxa de sucesso
- Tempo medio

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
WFL-F01-T1,[FRONT] WorkflowList,feature,4h
WFL-F02-T1,[FRONT] Canvas Component,feature,16h
WFL-F02-T2,[FRONT] Node Components,feature,8h
WFL-F08-T1,[FRONT] Edge Connections,feature,6h
WFL-F09-T1,[BACK] Test Execution API,feature,8h
WFL-F10-T1,[BACK] Activation API,feature,4h
WFL-F10-T2,[BACK] Execution Engine,feature,16h
WFL-F12-T1,[FRONT] ExecutionLogs,feature,5h
```

---

## 9. Padrao de Design

### Componentes
- Canvas com grid (React Flow ou custom)
- Nodes coloridos por tipo (trigger=verde, action=roxo)
- Edges com setas direcionais
- Panel de configuracao lateral

---

## 10. Uso de IA no Fluxo

**Este fluxo PODE utilizar IA para sugestoes de workflows.**

### Possibilidades
| Feature | Uso IA | Beneficio |
|---------|--------|-----------|
| Sugestao de workflow | Claude | Sugerir automacoes baseado em uso |
| Otimizacao | ML | Identificar gargalos |
| Templates inteligentes | Claude | Gerar templates por contexto |

---

# FLUXO 05: TEMPLATES DE COMUNICACAO

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Gestao de Templates de Comunicacao e Comandos LIA**

### O que esse fluxo entrega
Sistema de criacao e gestao de templates de comandos para a LIA, incluindo templates de busca, comunicacao, workflows e analises.

### Para qual usuario
- Recrutador
- Gestor de RH
- Administrador

### Resultado final esperado
Biblioteca de templates reutilizaveis para acelerar operacoes recorrentes com a LIA.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao | Arquivo |
|------------|-----------|---------|
| TemplatesPage | Pagina de templates | templates-page.tsx |
| TemplateCard | Card de template | templates-page.tsx |
| CreateTemplateModal | Modal de criacao | templates-page.tsx |
| TemplateFilters | Filtros e busca | templates-page.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/templates | GET | Listar templates |
| /api/v1/templates | POST | Criar template |
| /api/v1/templates/{id} | PUT | Editar |
| /api/v1/templates/{id} | DELETE | Excluir |
| /api/v1/templates/{id}/execute | POST | Executar |
| /api/v1/templates/{id}/duplicate | POST | Duplicar |

### Dados

| Tabela | Campos |
|--------|--------|
| command_templates | id, name, category, command, filters, tags |
| template_executions | template_id, user_id, success, timestamp |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| TPL-F01 | Listar Templates | Ver templates disponiveis |
| TPL-F02 | Criar Template | Novo template de comando |
| TPL-F03 | Editar Template | Alterar configuracao |
| TPL-F04 | Excluir Template | Remover template |
| TPL-F05 | Executar Template | Rodar comando LIA |
| TPL-F06 | Duplicar Template | Copiar para personalizacao |
| TPL-F07 | Compartilhar | Disponibilizar para equipe |
| TPL-F08 | Filtrar por Categoria | Busca, Comunicacao, etc |
| TPL-F09 | Ordenar | Por uso, data, sucesso |
| TPL-F10 | Ver Estatisticas | Uso e taxa de sucesso |

---

## 4. Documentacao Detalhada

### TPL-F02: Criar Template

#### Historia de Usuario
"Como recrutador, eu quero salvar comandos frequentes como templates para reutilizar."

#### Regras de Negocio
1. Nome obrigatorio e unico
2. Categorias: search, communication, workflow, analysis
3. Comando em linguagem natural
4. Filtros pre-definidos opcionais
5. Tags para organizacao
6. Tempo estimado de economia

#### Inputs
```json
{
  "name": "Devs React Senior SP",
  "description": "Busca desenvolvedores React senior em SP",
  "category": "search",
  "command": "Buscar desenvolvedores React senior em Sao Paulo com 5+ anos",
  "filters": {
    "skills": ["React", "TypeScript"],
    "seniority": ["Senior"],
    "locations": ["Sao Paulo, SP"]
  },
  "tags": ["frontend", "react", "senior"],
  "estimatedTime": 180
}
```

---

## 5. Cards de Especificacao

### CARD TPL-FLOW-001: Gestao de Templates

```yaml
Titulo: [FULL-STACK] Implementar Gestao de Templates LIA
Tipo: Feature
Sprint: 3
Pontos: 21

Requisitos Tecnicos:
  Frontend:
    - TemplateGrid responsivo
    - Modal de criacao/edicao
    - Filtros e busca
    - Execucao direta
  Backend:
    - CRUD /api/v1/templates
    - Integracao com LIA para execucao
    - Tracking de uso

DoD:
  - [ ] CRUD funciona
  - [ ] Executar redireciona para LIA
  - [ ] Estatisticas atualizam
  - [ ] Compartilhamento funciona
```

---

## 6. Diagrama da Jornada do Fluxo

```
INICIO
  |
  v
[Recrutador executa busca na LIA]
  |
  v
[Resultados satisfatorios]
  |
  v
[Clica em "Salvar como Template"]
  |
  v
[Modal de criacao abre]
  |
  v
[Comando pre-preenchido]
  |
  v
[Usuario adiciona nome e tags]
  |
  v
[Salva template]
  |
  v
[Template disponivel na biblioteca]
  |
  v
[Proxima vez: clica em "Executar"]
  |
  v
[LIA executa comando salvo]
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: CRUD Basico (Sprint 3)
- Criar, editar, excluir
- Listar com filtros

### Fase 2: Execucao (Sprint 3)
- Integrar com LIA
- Tracking de uso

### Fase 3: Compartilhamento (Sprint 4)
- Templates de equipe
- Templates publicos

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
TPL-F01-T1,[FRONT] TemplateGrid,feature,5h
TPL-F02-T1,[FRONT] CreateModal,feature,5h
TPL-F02-T2,[BACK] CRUD API,feature,4h
TPL-F05-T1,[FRONT] Execute Button,feature,3h
TPL-F05-T2,[BACK] LIA Integration,feature,4h
TPL-F10-T1,[FRONT] Stats Display,feature,3h
```

---

## 9. Padrao de Design

### Componentes
- Grid de cards responsivo (1-3 colunas)
- Badge de categoria com cor
- Metricas inline (usos, sucesso)
- Botoes de acao rapida

---

## 10. Uso de IA no Fluxo

**Este fluxo UTILIZA IA indiretamente.**

A execucao de templates aciona a LIA que processa o comando salvo. A criacao de templates nao usa IA, mas poderia:

| Feature | Uso IA | Beneficio |
|---------|--------|-----------|
| Sugestao de nome | Claude | Gerar nome baseado no comando |
| Otimizacao de comando | Claude | Melhorar query para melhores resultados |
| Auto-tagging | NLP | Extrair tags automaticamente |

---

# FLUXO 06: ONBOARDING E CALIBRACAO LIA

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Onboarding Automatizado e Calibracao da LIA**

### O que esse fluxo entrega
Sistema completo de onboarding de novos colaboradores aprovados, com Kanban de etapas, comunicacoes automaticas, gestao de documentos, e calibracao da personalidade da LIA.

### Para qual usuario
- Gestor de RH
- Administrador de RH

### Resultado final esperado
Novos colaboradores integrados de forma automatizada, com todas as etapas documentadas e LIA calibrada para a cultura da empresa.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao | Arquivo |
|------------|-----------|---------|
| OnboardingPage | Pagina basica | onboarding-page.tsx |
| OnboardingPremiumPage | Versao premium com Kanban | onboarding-premium-page.tsx |
| KanbanBoard | Board de etapas | onboarding-premium-page.tsx |
| CandidateCard | Card no Kanban | onboarding-premium-page.tsx |
| TemplatesManager | Templates de mensagens | onboarding-premium-page.tsx |
| LIATab | Configuracao da LIA | settings-page.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/onboarding | GET | Listar processos |
| /api/v1/onboarding | POST | Iniciar onboarding |
| /api/v1/onboarding/{id} | PUT | Atualizar estagio |
| /api/v1/onboarding/{id}/documents | GET | Listar documentos |
| /api/v1/onboarding/{id}/communications | POST | Enviar comunicacao |
| /api/v1/settings/lia | GET | Config LIA |
| /api/v1/settings/lia | PUT | Atualizar LIA |
| /api/v1/settings/lia/calibrate | POST | Calibrar LIA |

### Dados

| Tabela | Campos |
|--------|--------|
| onboarding_processes | id, candidate_id, stage, progress |
| onboarding_documents | process_id, type, status, url |
| onboarding_communications | process_id, type, sent_at |
| lia_settings | company_id, personality, style, features |

### IA

| Componente | Modelo | Funcao |
|------------|--------|--------|
| LIA Calibration | Claude | Ajustar personalidade e estilo |
| Auto-communications | Claude | Personalizar mensagens |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| ONB-F01 | Ver Kanban | Board de etapas de onboarding |
| ONB-F02 | Mover Candidato | Drag-drop entre estagios |
| ONB-F03 | Enviar Boas-vindas | Email/WhatsApp automatico |
| ONB-F04 | Solicitar Documentos | Checklist de documentos |
| ONB-F05 | Verificar Documentos | Aprovar/rejeitar uploads |
| ONB-F06 | Agendar Exames | Exames admissionais |
| ONB-F07 | Configurar Acessos | Sistemas e equipamentos |
| ONB-F08 | Agendar Primeiro Dia | Cronograma de integracao |
| ONB-F09 | Ver Analytics | Metricas de onboarding |
| LIA-F01 | Configurar Personalidade | Estilo de comunicacao |
| LIA-F02 | Habilitar Features | Sugestoes, insights, etc |
| LIA-F03 | Calibrar LIA | Ajuste fino com exemplos |

---

## 4. Documentacao Detalhada

### LIA-F03: Calibrar LIA

#### Historia de Usuario
"Como administrador, eu quero calibrar a LIA para que ela se comunique de acordo com a cultura da empresa."

#### Regras de Negocio
1. 4 estilos de personalidade disponiveis
2. Toggle para features individuais
3. Exemplos de comunicacao para calibracao
4. Preview de respostas calibradas
5. Reset para padrao disponivel

#### Formulas e Logicas
```
Personalidades disponiveis:
  - professional: Formal e objetiva
  - casual: Amigavel e descontraida
  - concise: Respostas curtas
  - detailed: Explicacoes completas

Features toggleaveis:
  - autoSuggestions: Sugestoes proativas
  - contextAwareness: Contexto de conversas
  - proactiveInsights: Alertas automaticos
  - learningMode: Aprender preferencias

Calibracao:
  1. Usuario fornece exemplos de comunicacao ideal
  2. Claude analisa padrao
  3. Ajusta parametros internos
  4. Gera preview para aprovacao
```

#### Inputs
```json
{
  "personality": "professional",
  "responseStyle": "detailed",
  "features": {
    "autoSuggestions": true,
    "contextAwareness": true,
    "proactiveInsights": true,
    "learningMode": true
  },
  "calibration_examples": [
    "Exemplo de email formal...",
    "Exemplo de resposta ao candidato..."
  ]
}
```

---

## 5. Cards de Especificacao

### CARD ONB-FLOW-001: Onboarding Kanban Premium

```yaml
Titulo: [FULL-STACK] Implementar Onboarding Kanban
Tipo: Epic
Sprint: 4-5
Pontos: 55

Descricao: |
  Sistema de onboarding com Kanban visual, automacoes de
  comunicacao, gestao de documentos e exames.

Requisitos Tecnicos:
  Frontend:
    - KanbanBoard com drag-drop
    - CandidateCard com progresso
    - Modal de detalhes
    - Templates de comunicacao
  Backend:
    - CRUD onboarding
    - Envio de emails/WhatsApp
    - Upload de documentos
    - Agendamento de tarefas
  Dados:
    - onboarding_processes
    - onboarding_documents
    - onboarding_communications

DoD:
  - [ ] Kanban renderiza
  - [ ] Drag-drop funciona
  - [ ] Comunicacoes enviam
  - [ ] Documentos fazem upload
```

---

## 6. Diagrama da Jornada do Fluxo

### Onboarding de Novo Colaborador

```
INICIO
  |
  v
[Candidato aprovado em vaga]
  |
  v
[Aparece em "Boas-vindas" no Kanban]
  |
  v
[Sistema envia email automatico]
  |
  +-- Personalized com dados do candidato
  |
  v
[RH arrasta para "Documentacao"]
  |
  v
[Sistema envia checklist de documentos]
  |
  v
[Candidato faz upload de docs]
  |
  v
[RH verifica e aprova documentos]
  |
  v
[Arrasta para "Exames"]
  |
  v
[Sistema agenda exame admissional]
  |
  v
[Resultado do exame aprovado]
  |
  v
[Arrasta para "Sistemas"]
  |
  v
[TI cria acessos automaticamente]
  |
  v
[Arrasta para "Integracao"]
  |
  v
[Agenda de primeiro dia criada]
  |
  v
[Arrasta para "Concluido"]
  |
  v
[Colaborador integrado!]
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: Kanban Basico (Sprint 4)
- Board com etapas
- Drag-drop
- Cards de candidatos

### Fase 2: Comunicacoes (Sprint 4)
- Templates de mensagens
- Envio automatico
- Variaveis dinamicas

### Fase 3: Documentos (Sprint 5)
- Checklist de docs
- Upload e verificacao
- Status de aprovacao

### Fase 4: Integracoes (Sprint 5)
- Exames admissionais
- Criacao de acessos
- Agenda de primeiro dia

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
ONB-F01-T1,[FRONT] KanbanBoard,feature,10h
ONB-F02-T1,[FRONT] DragDrop Logic,feature,6h
ONB-F03-T1,[BACK] Email Templates,feature,5h
ONB-F03-T2,[BACK] Send Email API,feature,4h
ONB-F04-T1,[FRONT] DocChecklist,feature,5h
ONB-F05-T1,[FRONT] DocVerification,feature,5h
LIA-F01-T1,[FRONT] PersonalitySelector,feature,4h
LIA-F02-T1,[FRONT] FeatureToggles,feature,3h
LIA-F03-T1,[BACK] Calibration API,feature,6h
```

---

## 9. Padrao de Design

### Componentes Kanban
- Colunas com header colorido
- Cards arrastáveis
- Badge de progresso
- Avatar do candidato

---

## 10. Uso de IA no Fluxo

**Este fluxo UTILIZA IA para calibracao da LIA.**

### Detalhes
| Aspecto | Especificacao |
|---------|---------------|
| Modelo | Claude Sonnet |
| Funcao | Ajustar parametros de comunicacao |
| Input | Exemplos de comunicacao ideal |
| Output | Parametros calibrados |

---

# FLUXO 07: CONFIGURACAO DE BENEFICIOS E CULTURA

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Configuracao de Cultura Organizacional e Beneficios**

### O que esse fluxo entrega
Sistema para definir missao, visao, valores, beneficios oferecidos, e caracteristicas da marca empregadora.

### Para qual usuario
- Administrador de RH
- Gestor de RH

### Resultado final esperado
Pagina de cultura completa para atrair candidatos e alinhar contratacoes com valores da empresa.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao | Arquivo |
|------------|-----------|---------|
| CultureTab | Aba de cultura | settings-page.tsx |
| BenefitsEditor | Editor de beneficios | settings-page.tsx |
| ValuesEditor | Editor de valores | settings-page.tsx |
| EVPEditor | Employer Value Proposition | settings-page.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/company/culture | GET | Obter cultura |
| /api/v1/company/culture | PUT | Atualizar cultura |
| /api/v1/company/benefits | GET | Listar beneficios |
| /api/v1/company/benefits | PUT | Atualizar beneficios |

### Dados

| Tabela | Campos |
|--------|--------|
| company_culture | mission, vision, values[], evp |
| company_benefits | id, category, name, description, icon |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| CUL-F01 | Definir Missao | Texto da missao |
| CUL-F02 | Definir Visao | Texto da visao |
| CUL-F03 | Adicionar Valor | Valor da empresa |
| CUL-F04 | Editar Valor | Alterar texto |
| CUL-F05 | Ordenar Valores | Prioridade dos valores |
| CUL-F06 | Adicionar Beneficio | Novo beneficio |
| CUL-F07 | Categorizar Beneficio | Saude, Educacao, etc |
| CUL-F08 | Definir EVP | Proposta de valor |
| CUL-F09 | Preview Pagina | Ver como candidato ve |

---

## 4. Documentacao Detalhada

### CUL-F03: Adicionar Valor

#### Regras de Negocio
1. Titulo do valor (3-50 chars)
2. Descricao opcional (max 200 chars)
3. Icone selecionavel
4. Maximo 10 valores
5. Drag-drop para ordenar

#### Inputs
```json
{
  "title": "Inovacao",
  "description": "Buscamos constantemente novas formas de fazer",
  "icon": "lightbulb"
}
```

---

## 5. Cards de Especificacao

### CARD CUL-FLOW-001: Cultura Organizacional

```yaml
Titulo: [FULL-STACK] Implementar Config. de Cultura
Tipo: Feature
Sprint: 2
Pontos: 13

Requisitos Tecnicos:
  Frontend:
    - TextAreas para missao/visao
    - Lista editavel de valores
    - Grid de beneficios
  Backend:
    - CRUD cultura/beneficios

DoD:
  - [ ] Missao/visao editaveis
  - [ ] Valores CRUD funciona
  - [ ] Beneficios CRUD funciona
  - [ ] Preview funciona
```

---

## 6-10. [Seções seguem padrão dos fluxos anteriores]

---

# FLUXO 08: GESTAO DE PERGUNTAS E TESTES

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Configuracao de Criterios de Avaliacao e Assessment**

### O que esse fluxo entrega
Sistema para definir criterios de avaliacao, perguntas de entrevista, testes tecnicos e scorecards.

### Para qual usuario
- Gestor de Recrutamento
- Tech Lead
- Administrador de RH

### Resultado final esperado
Biblioteca de criterios e perguntas reutilizaveis para avaliar candidatos de forma consistente.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao | Arquivo |
|------------|-----------|---------|
| AssessmentTab | Aba de assessment | settings-page.tsx |
| CriteriaEditor | Editor de criterios | settings-page.tsx |
| QuestionsBank | Banco de perguntas | settings-page.tsx |
| ScorecardBuilder | Construtor de scorecard | settings-page.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/assessment/criteria | GET/POST | CRUD criterios |
| /api/v1/assessment/questions | GET/POST | CRUD perguntas |
| /api/v1/assessment/scorecards | GET/POST | CRUD scorecards |

### Dados

| Tabela | Campos |
|--------|--------|
| assessment_criteria | id, name, category, weight |
| assessment_questions | id, text, type, criteria_id |
| scorecards | id, name, criteria_ids, questions_ids |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| ASS-F01 | Criar Criterio | Novo criterio de avaliacao |
| ASS-F02 | Definir Peso | Peso do criterio no score |
| ASS-F03 | Criar Pergunta | Nova pergunta de entrevista |
| ASS-F04 | Vincular Criterio | Pergunta avalia criterio |
| ASS-F05 | Criar Scorecard | Template de avaliacao |
| ASS-F06 | Selecionar Criterios | Montar scorecard |
| ASS-F07 | Ordenar Perguntas | Sequencia da entrevista |
| ASS-F08 | Preview Scorecard | Ver como fica |
| ASS-F09 | Duplicar Scorecard | Copiar para editar |

---

## 4-10. [Seções seguem padrão dos fluxos anteriores]

---

## APENDICE: INTEGRAÇÕES DE COMUNICACAO

### Slack e Teams (integrations-page.tsx)

Sistema de integracao com Slack e Microsoft Teams para notificacoes automaticas:

| Funcionalidade | Descricao |
|----------------|-----------|
| Conectar Webhook | Configurar URL de webhook |
| Configurar Canais | Selecionar canais de destino |
| Definir Eventos | Quais eventos notificam |
| Templates de Mensagem | Formato das notificacoes |
| Logs de Envio | Historico de mensagens |
| Testar Conexao | Verificar webhook ativo |

### Eventos Disponiveis
- novo_candidato: Novo candidato aplicou
- aprovacao: Candidato aprovado
- aprovacao_lote: Aprovacao em massa
- nova_nota: Nota adicionada
- mencao: Usuario mencionado
- entrevista_agendada: Entrevista marcada

---

## RESUMO DE ESTIMATIVAS

| Fluxo | Story Points | Sprints |
|-------|-------------|---------|
| 01 - Config. Empresa | 55 | 1-2 |
| 02 - Usuarios/Permissoes | 34 | 2-3 |
| 03 - Integracao ATS | 55 | 3-4 |
| 04 - Automacoes | 55 | 4-5 |
| 05 - Templates | 21 | 3 |
| 06 - Onboarding/LIA | 55 | 4-5 |
| 07 - Cultura/Beneficios | 13 | 2 |
| 08 - Assessment | 21 | 3 |
| **TOTAL** | **309** | **8-10** |

---

*Documento gerado em Dezembro 2024 - Plataforma LIA v1.0*
