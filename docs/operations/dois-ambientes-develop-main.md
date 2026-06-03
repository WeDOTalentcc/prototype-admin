# Dois ambientes publicados: `develop` e `main`

**Status:** guia operacional para o time. **Idioma:** PT-BR.
**Objetivo:** ter dois Repls publicados, espelhados via GitHub, cada um com sua
URL, banco e secrets próprios — um para desenvolver/testar (`develop`) e outro
estável para o time consumir (`main`).

> ⚠️ Nenhum dos dois é produção real com SLA. Ambos servem a testes /
> desenvolvimento / consumo interno. "Produção" aqui significa "a versão estável
> que os devs olham no dia a dia".

---

## 1. Por que dois Repls (e não um só)

Um Repl publica **uma única URL**. Não dá para o mesmo Repl publicar duas
branches como dois ambientes ao vivo. Por isso são necessários **dois Repls**:

| Repl | Papel | Branch que segue | Domínio (fase posterior) |
|---|---|---|---|
| **Este Repl** | desenvolvimento / testes (workspace sempre mais novo; publicado = ambiente de testes) | `develop` | `dev.prototype.wedotalent.cc` |
| **Repl forkado** | "produção" / consumo dos devs | `main` | `demo.prototype.wedotalent.cc` |

**Princípio central:** existe **um único código-fonte vivendo no GitHub**
(`WeDOTalentcc/prototype`), com duas branches. O que fica sincronizado é o
**código**, não "o fork". O fork é usado **uma única vez** para criar o segundo
Repl; depois disso, a sincronização é **só via GitHub** (nunca mais re-fork).

---

## 2. ⛔ Repositório proibido

> O repositório **`WeDOTalentcc/wedotalent02202026`** NÃO faz parte deste
> projeto e **NUNCA** deve ser usado como origem ou destino destes ambientes.
> Hoje este Repl ainda tem um remote `wedotalent` apontando para ele —
> **remova/desconecte** esse remote e garanta que nenhum push, pull ou publish
> vá para lá. O único repositório válido é **`WeDOTalentcc/prototype`**
> (`https://github.com/WeDOTalentcc/prototype.git`).

---

## 3. Passo a passo (executar uma vez)

> Estes passos são feitos pela **interface do Replit / GitHub / WorkOS** — não
> por linha de comando dentro do código. O controle de versão do Replit é
> gerenciado pela plataforma.

### Passo 1 — Re-apontar este Repl para o `prototype`
1. Abra o painel **Git** deste Repl (ícone de controle de versão na barra lateral).
2. **Desconecte** a conexão atual (que aponta para `wedotalent02202026`).
3. **Conecte** ao repositório `WeDOTalentcc/prototype`
   (`https://github.com/WeDOTalentcc/prototype.git`).
4. Confirme a autenticação (Replit ↔ GitHub) e valide que nenhuma operação
   aponta mais para o repositório proibido.

### Passo 2 — Criar as branches e fazer o push inicial
1. No GitHub (ou pelo painel Git do Replit), garanta que existam as branches
   **`main`** (produção) e **`develop`** (desenvolvimento).
2. Faça o **push** do código atual deste Repl para a branch **`develop`**.
3. Valide no GitHub que o código chegou em `develop`.
   *(A criação das branches pode ser delegada ao time de devs, se preferir.)*

### Passo 3 — Confirmar este Repl como ambiente de dev/testes
- Este Repl é o trabalho diário e publica o ambiente de **testes**. Todo o
  trabalho daqui empurra (push) para **`develop`**.
- Gesto de "enviar": painel **Git** → **Commit & Push** para `develop`.

### Passo 4 — Criar o Repl de produção (`main`) via fork
1. **Forke este Repl uma única vez** (menu do Repl → *Fork*). Esse novo Repl
   será o ambiente de **produção/consumo**.
2. No Repl forkado, abra o painel **Git** e conecte-o ao **mesmo** repositório
   `WeDOTalentcc/prototype`, configurando-o para seguir a branch **`main`**.
3. A partir daqui, os dois Repls só se falam **via GitHub** — nunca mais re-fork.

### Passo 5 — Isolar o banco de dados em cada ambiente
- Cada Repl precisa do **seu próprio** PostgreSQL (e Redis, se aplicável), para
  que quebrar o ambiente de testes nunca afete o de produção.
- No Repl forkado (produção), **provisione um banco próprio** e rode as
  migrações:
  ```bash
  bash scripts/post-merge.sh   # instala deps + roda `alembic upgrade head`
  ```
  *(Este script já é executado automaticamente após cada merge — ver `[postMerge]` no `.replit`.)*
- **Nunca** compartilhe a mesma `DATABASE_URL` entre os dois Repls.

### Passo 6 — Isolar os secrets em cada ambiente
- Cada Repl recebe **seu próprio conjunto de secrets** (use a aba *Secrets* do
  Replit). Dê preferência a **chaves de teste/sandbox**.
- **Nenhum secret compartilhado** entre os dois ambientes. Pelo menos:
  `SECRET_KEY`, `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_SESSION_SECRET`,
  `WORKOS_WEBHOOK_SECRET`, chaves de LLM e demais integrações.
- Lembrete: em produção o `SECRET_KEY` **não pode** ser
  `change-this-in-production` (o boot falha — ver validador em
  `lia-agent-system/libs/config/lia_config/config.py`).

### Passo 7 — Configurar URLs e login por ambiente
A configuração já é **toda via variáveis de ambiente** — não há URL hardcoded a
mudar no código. Ajuste estes valores em **cada** Repl apontando para a URL
daquele Repl:

| Variável | Onde | `develop` (testes) | `main` (produção) |
|---|---|---|---|
| `APP_ENV` | backend | `development` | `production` |
| `CORS_ORIGINS` | backend | URL do Repl de dev | URL do Repl de prod |
| `NEXT_PUBLIC_APP_URL` | frontend | URL do Repl de dev | URL do Repl de prod |
| `WORKOS_REDIRECT_URI` | frontend | `https://<url-dev>/api/auth/workos/callback` | `https://<url-prod>/api/auth/workos/callback` |
| `WORKOS_API_KEY` / `WORKOS_CLIENT_ID` | frontend | chaves do ambiente de dev | chaves do ambiente de prod |
| `BACKEND_URL` | frontend | `http://127.0.0.1:8001` | `http://127.0.0.1:8001` |

> No deploy VM atual, frontend e backend rodam no mesmo Repl, então
> `BACKEND_URL` continua loopback (`127.0.0.1:8001`) nos dois ambientes.

**WorkOS (painel `dashboard.workos.com`):** registre a URL de **cada** ambiente
como *redirect/callback* permitido, senão o login quebra:
- `https://<url-dev>/api/auth/workos/callback`
- `https://<url-prod>/api/auth/workos/callback`

### Passo 8 — Publicar cada ambiente
1. Publique o Repl de **dev** (este) → gera a URL `.replit.app` do ambiente de testes.
2. Publique o Repl de **produção** (forkado) → gera a URL `.replit.app` própria.
3. Valide **login e acesso** em ambos.

> O botão **Publish** é acionado pelo usuário na versão principal de cada Repl
> (um agente de task não publica). A config de deploy já está pronta no
> `.replit` (`deploymentTarget = "vm"`).

---

## 4. 🔁 Ritual de promover `develop → main` (dia a dia)

```
1. Trabalha NESTE Repl (dev).
2. Commit & Push para a branch `develop`  → atualiza o ambiente de testes.
3. Testa no ambiente de dev publicado.
4. Quando aprovado: no GitHub, abre PR / faz merge de `develop` → `main`.
5. No Repl de produção: painel Git → Pull da branch `main`.
6. No Repl de produção: clicar Publish (republicar).
```

- **Sentido único:** o código sempre flui `develop → main`. Não promova nada que
  não tenha passado pelo ambiente de testes.
- Migrações de banco entram automaticamente no pull (via `scripts/post-merge.sh`
  → `alembic upgrade head`).

---

## 5. ✂️ Trecho para entregar ao time de devs

> **Como mexer nos dois ambientes**
>
> - Existe **um único repositório** no GitHub: `WeDOTalentcc/prototype`, com duas
>   branches: `develop` (testes) e `main` (estável).
> - **Repl de dev** → segue `develop`, é onde se desenvolve e pode quebrar.
> - **Repl de produção** → segue `main`, é a versão estável que consumimos.
> - **Para subir algo novo:** trabalhe no Repl de dev → *Commit & Push* para
>   `develop` → teste no ambiente de dev publicado.
> - **Para promover:** abra PR `develop → main` no GitHub → após merge, no Repl
>   de produção faça *Pull* de `main` e clique em *Publish*.
> - **Bancos e secrets são separados** entre os dois ambientes — quebrar o de
>   testes **não** afeta o de produção.
> - ⛔ **Nunca** use o repositório `WeDOTalentcc/wedotalent02202026` para nada.

---

## 6. (Fase posterior) Domínios customizados

Depois de confirmar o mapeamento com o time:
1. Anexe `dev.prototype.wedotalent.cc` ao Repl de **dev** e
   `demo.prototype.wedotalent.cc` ao Repl de **produção** (Publishing → Custom
   domain), e configure o DNS.
2. Acrescente cada novo domínio ao `CORS_ORIGINS` e aos *redirects/callbacks* do
   WorkOS do ambiente correspondente.
3. Revalide o login em cada domínio.

> **Decisão a confirmar:** `dev.prototype` → `develop` e `demo.prototype` →
> `main`, ou invertido? É só etiqueta de endereço — não muda código.

---

## 7. Fora de escopo

- Compra/registro do domínio `wedotalent.cc` (assume-se já existente).
- CI/CD avançado (GitHub Actions, testes automáticos no merge).
- Produção real com SLA/observabilidade dedicada.
- Migração de dados reais entre ambientes.
- Ambientes por pessoa (o desenho é **dois ambientes compartilhados** pelo time).
