# Code Review — Entity Page Feature

## Resumo

Revisão focada em **segurança** e **boas práticas** da feature `entity_page` (backend Rails + frontend Vue/Nuxt).

---

## Problemas Encontrados

### 🔴 Crítico

#### 1. IDOR no `destroy` — Falta de scoping por `user_id` no `update`

**Arquivo:** `app/controllers/v1/users/entity_pages_controller.rb`

O `set_entity_page` valida `user_id` corretamente para `show`, `update` e `destroy`. Porém, o `update` permite que um usuário altere o `user_id` ou `account_id` via params se não forem filtrados — embora `entity_page_params` não permita esses campos, o risco está coberto. **OK — sem falha real**, mas vale validar que `permit` nunca inclua `user_id`/`account_id`.

**Status:** ✅ Coberto pelo `permit` atual.

#### 2. `pages: {}` permite JSONB arbitrário sem limites de tamanho

**Arquivo:** `app/controllers/v1/users/entity_pages_controller.rb` (linha 52)

```ruby
params.require(:entity_page).permit(:entity, :type_view, :custom_entity, :job_id, pages: {})
```

O `pages: {}` permite **qualquer estrutura JSON** sem validação de profundidade ou tamanho. Um atacante pode enviar payloads gigantes (MB de JSON) causando:
- Consumo excessivo de storage no PostgreSQL
- Lentidão em serialização/desserialização
- Potencial DoS por consumo de memória

**Recomendação:** Adicionar validação de tamanho no model:

```ruby
validate :pages_size_limit

private

def pages_size_limit
  return if pages.blank?
  errors.add(:pages, "is too large (max 64KB)") if pages.to_json.bytesize > 64.kilobytes
end
```

**Severidade:** 🔴 Alta

---

### 🟡 Médio

#### 3. `destroy_all` sem confirmação ou rate limiting

**Arquivo:** `app/controllers/v1/users/entity_pages_controller.rb` (linha 38)

```ruby
def destroy_all
  EntityPage.where(user_id: @current_user.id).destroy_all
end
```

`destroy_all` instancia cada record e roda callbacks. Se o usuário tiver muitos registros, isso é lento. Use `delete_all` já que não há callbacks relevantes:

```ruby
def destroy_all
  EntityPage.where(user_id: @current_user.id).delete_all
  head :no_content
end
```

**Severidade:** 🟡 Média

#### 4. Falta de limite de registros por usuário

**Arquivo:** `app/models/entity_page.rb`

Não há limite de quantos `entity_pages` um usuário pode criar. Um script automatizado pode criar milhares de registros com combinações únicas de `entity/type_view/link/custom_entity`.

**Recomendação:** Adicionar validação:

```ruby
validate :max_pages_per_user, on: :create

def max_pages_per_user
  return if EntityPage.where(user_id: user_id).count < 100
  errors.add(:base, "maximum entity pages reached")
end
```

**Severidade:** 🟡 Média

#### 5. Unique index com colunas nullable pode não prevenir duplicatas

**Arquivo:** `db/migrate/20260408120000_add_unique_index_to_entity_pages.rb`

O índice inclui `link` e `custom_entity`, que são **nullable**. No PostgreSQL, `NULL != NULL`, então duas rows com `link = NULL` e mesmos demais campos **não violam** o índice único.

**Impacto:** O upsert no model faz `find_by` com `link: nil`, que funciona corretamente. Mas a proteção a nível de banco não existe para combinações com NULL.

**Recomendação:** Usar `COALESCE` no índice ou adicionar validação de unicidade no model:

```ruby
validates :entity, uniqueness: {
  scope: %i[user_id type_view link custom_entity],
  message: "already exists for this combination"
}
```

**Severidade:** 🟡 Média

#### 6. Frontend: `pageLink` construído por concatenação de string

**Arquivo:** `components/ui/menu/EntityPageMenu.vue` (linha 87)

```javascript
function pageLink(page) {
  if (page.pages?.query) {
    return `${page.pages.link}?${page.pages.query}`
  }
  return page.pages?.link || '/'
}
```

O conteúdo de `pages.link` e `pages.query` vem do banco (originalmente enviado pelo usuário). Se alguém injetar `javascript:alert(1)` no campo `link`, o `<v-btn :to="...">` do Vue Router trata como rota interna, então **não há XSS** via `router-link`. Porém, links externos ou esquemas perigosos poderiam ser passados.

**Recomendação:** Validar que `link` começa com `/`:

```javascript
function pageLink(page) {
  const link = page.pages?.link || '/'
  if (!link.startsWith('/')) return '/'
  if (page.pages?.query) return `${link}?${page.pages.query}`
  return link
}
```

**Severidade:** 🟡 Média

---

### 🟢 Baixo / Boas Práticas

#### 7. Model: `upsert_page` não roda dentro de transaction

**Arquivo:** `app/models/entity_page.rb`

O `find_by` + `create` tem uma race condition teórica. Dois requests simultâneos com a mesma combinação podem ambos passar pelo `find_by` e tentar `create`. O índice único no banco protege contra duplicatas (levantando `ActiveRecord::RecordNotUnique`), mas o erro não é tratado.

**Recomendação:**

```ruby
def self.upsert_page(user, params)
  transaction do
    current_page = find_by(...)
    # ...
  end
rescue ActiveRecord::RecordNotUnique
  retry
end
```

**Severidade:** 🟢 Baixa (raro em uso real)

#### 8. Serializer expõe `user_id` e `account_id`

**Arquivo:** `app/serializer/entity_page_serializer.rb`

O serializer expõe `user_id` e `account_id` no response. Esses campos são desnecessários para o frontend (o usuário já sabe seu próprio ID) e expõem IDs internos.

**Recomendação:** Remover `user_id` e `account_id` do serializer.

**Severidade:** 🟢 Baixa

#### 9. Frontend: erro silenciado em `savePage` e `fetchPages`

**Arquivo:** `composables/useEntityPages.ts`

```typescript
catch {
  // silent
}
```

Erros são completamente ignorados. Se a API retorna 500, o usuário não tem feedback.

**Recomendação:** Logar no `console.error` no mínimo, ou mostrar toast para erros não-esperados.

**Severidade:** 🟢 Baixa

#### 10. Spec: falta teste de autorização cruzada (IDOR)

**Arquivo:** `spec/requests/v1/users/entity_pages_controller_spec.rb`

Não há teste para garantir que um usuário **não consiga** acessar/deletar entity pages de **outro** usuário. Isso é a validação mais importante de segurança.

**Recomendação:** Adicionar:

```ruby
context "when trying to access another user's entity page" do
  let(:other_user) { create(:user) }
  let(:other_page) { create(:entity_page, user: other_user, account: other_user.account) }

  it "returns not found" do
    delete "/v1/users/entity_pages/#{other_page.id}", headers: auth_headers(user)
    expect(response).to have_http_status(:not_found)
  end
end
```

**Severidade:** 🟢 Baixa (funcionalidade está correta, falta cobertura de teste)

---

## Checklist de Correções

| # | Severidade | Descrição | Arquivo |
|---|-----------|-----------|---------|
| 2 | 🔴 Alta | Validar tamanho máximo do JSONB `pages` | `entity_page.rb` |
| 3 | 🟡 Média | Usar `delete_all` em vez de `destroy_all` | `entity_pages_controller.rb` |
| 4 | 🟡 Média | Limitar registros por usuário (max 100) | `entity_page.rb` |
| 5 | 🟡 Média | Adicionar `validates :uniqueness` no model | `entity_page.rb` |
| 6 | 🟡 Média | Validar prefixo `/` no link do frontend | `EntityPageMenu.vue` |
| 7 | 🟢 Baixa | Tratar race condition com `rescue RecordNotUnique` | `entity_page.rb` |
| 8 | 🟢 Baixa | Remover `user_id`/`account_id` do serializer | `entity_page_serializer.rb` |
| 9 | 🟢 Baixa | Logar erros no frontend | `useEntityPages.ts` |
| 10 | 🟢 Baixa | Adicionar teste IDOR no spec | `entity_pages_controller_spec.rb` |

---

## Pontos Positivos

- ✅ Controller usa `@current_user.id` para scoping — proteção IDOR correta
- ✅ `entity_page_params` usa `permit` explícito (não `permit!` como antes)
- ✅ `set_entity_page` filtra por `user_id` — impede acesso cruzado
- ✅ Todas as rotas estão dentro de `namespace :users` (autenticação obrigatória)
- ✅ Frontend usa optimistic update com rollback em caso de erro
- ✅ `frozen_string_literal: true` em todos os arquivos Ruby
- ✅ Índice único no banco para prevenir duplicatas
- ✅ Upsert centralizado no model (não no controller)
