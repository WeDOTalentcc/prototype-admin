---
applyTo: "plataforma-lia/src/**/*.tsx"
---

# Forms & Validation — WeDO Talent

Todo formulário novo usa **React Hook Form + Zod** via `@hookform/resolvers`. Ambos já estão instalados. Evite forms 100% controlados via `useState` — só aceitável para forms triviais (1-2 campos sem validação).

> ⚠️ Parte dos forms legados do projeto usa `useState` cru (ex. `screening-config/ScreeningStatusModal.tsx`). Migrar ao tocar.

## Schema primeiro

Defina o schema Zod em `src/lib/schemas/<dominio>.schema.ts`. Os tipos vêm da inferência — **não** duplique com `interface`.

```ts
// ✅ src/lib/schemas/job.schema.ts
import { z } from 'zod'

export const jobCreateSchema = z.object({
  title: z.string().min(1, 'Título é obrigatório'),
  description: z.string().max(5000).optional(),
  department: z.string().optional(),
  employment_type: z.enum(['clt', 'pj', 'internship', 'temporary']).optional(),
  salary_min: z.number().int().nonnegative().optional(),
  salary_max: z.number().int().nonnegative().optional(),
  remote: z.boolean().default(false),
}).refine(
  (data) => !data.salary_min || !data.salary_max || data.salary_max >= data.salary_min,
  { message: 'Salário máximo deve ser >= mínimo', path: ['salary_max'] },
)

export type JobCreateInput = z.infer<typeof jobCreateSchema>
```

```ts
// ❌ tipo duplicado — sai de sincronia
export interface JobCreateInput {
  title: string
  description?: string
  // ...
}
```

### Mensagens em português

Erros de validação são exibidos ao usuário — escreva em PT-BR. Se a label depender de i18n, passe a string traduzida no `message`:

```ts
// ✅
z.string().min(1, t('jobs.form.title_required'))
```

## Estrutura do componente

```tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { jobCreateSchema, type JobCreateInput } from '@/lib/schemas/job.schema'
import { extractErrorMessage } from '@/lib/api/extract-error-message'

interface CreateJobFormProps {
  onSuccess: (job: { id: string }) => void
  onCancel?: () => void
}

export function CreateJobForm({ onSuccess, onCancel }: CreateJobFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    reset,
  } = useForm<JobCreateInput>({
    resolver: zodResolver(jobCreateSchema),
    defaultValues: { remote: false },
  })

  const onSubmit = async (values: JobCreateInput) => {
    const res = await fetch('/api/backend-proxy/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      applyServerErrors(body, setError)
      toast.error(extractErrorMessage(body, res.status))
      return
    }

    const job = await res.json()
    toast.success('Vaga criada')
    reset()
    onSuccess(job)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <Field label="Título" error={errors.title?.message}>
        <Input id="title" {...register('title')} aria-invalid={!!errors.title} />
      </Field>

      <Field label="Descrição" error={errors.description?.message}>
        <Textarea id="description" {...register('description')} />
      </Field>

      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
        )}
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Criando...' : 'Criar vaga'}
        </Button>
      </div>
    </form>
  )
}
```

## Componente `Field`

Repetir label + erro em todo campo polui. Extraia um wrapper simples:

```tsx
// ✅ src/components/ui/field.tsx
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface FieldProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
  className?: string
}

export function Field({ label, error, required, children, className }: FieldProps) {
  return (
    <div className={cn('space-y-1.5', className)}>
      <Label>
        {label}
        {required && <span className="ml-1 text-status-error" aria-label="obrigatório">*</span>}
      </Label>
      {children}
      {error && (
        <p role="alert" className="text-xs text-status-error">
          {error}
        </p>
      )}
    </div>
  )
}
```

## Erros do servidor → campos

A API pode devolver dois shapes dependendo do backend. Trate **ambos** no helper:

```ts
// Rails:    { errors: ["Email já em uso", "Nome é obrigatório"] }
// FastAPI:  { detail: [{ loc: ['body','email'], msg: 'already exists' }, ...] }
// Proxy:    { error: "...", details: { errors | detail | message } }
```

Mapeie para `setError` do RHF quando possível:

```ts
// ✅ src/lib/api/apply-server-errors.ts
import type { FieldValues, UseFormSetError, Path } from 'react-hook-form'

interface ServerErrorBody {
  errors?: string[]
  detail?: Array<{ loc?: (string | number)[]; msg?: string }>
  details?: { errors?: Record<string, string[]>; detail?: unknown }
}

export function applyServerErrors<T extends FieldValues>(
  body: unknown,
  setError: UseFormSetError<T>,
): void {
  if (!body || typeof body !== 'object') return
  const err = body as ServerErrorBody

  // FastAPI detail array
  if (Array.isArray(err.detail)) {
    for (const item of err.detail) {
      const path = item.loc?.filter((p) => p !== 'body').join('.') ?? ''
      if (path && item.msg) {
        setError(path as Path<T>, { type: 'server', message: item.msg })
      }
    }
    return
  }

  // Rails `{ errors: ["..."] }` — não tem campo, vira root
  if (Array.isArray(err.errors) && err.errors.length > 0) {
    setError('root.server' as Path<T>, {
      type: 'server',
      message: err.errors.join(', '),
    })
    return
  }

  // Proxy wrapper
  if (err.details?.errors && typeof err.details.errors === 'object') {
    for (const [field, messages] of Object.entries(err.details.errors)) {
      if (Array.isArray(messages) && messages[0]) {
        setError(field as Path<T>, { type: 'server', message: messages[0] })
      }
    }
  }
}
```

Uso:

```tsx
if (!res.ok) {
  const body = await res.json().catch(() => ({}))
  applyServerErrors(body, setError)
  toast.error(extractErrorMessage(body, res.status))
  return
}
```

E exiba o erro global:

```tsx
{errors.root?.server && (
  <p role="alert" className="text-sm text-status-error">
    {errors.root.server.message}
  </p>
)}
```

## Submissão

- Desabilite o submit enquanto `isSubmitting`.
- Nunca deixe o botão clicável durante submit — duplica request.
- Use `noValidate` no `<form>` — a validação é Zod, não HTML5.
- Após sucesso, `reset()` e `onSuccess(data)` — deixe o pai decidir navegação/fechamento.
- Após falha, mostre toast + mantenha valores digitados.

```tsx
// ✅
<Button type="submit" disabled={isSubmitting}>
  {isSubmitting ? 'Salvando...' : 'Salvar'}
</Button>

// ❌ sem disabled
<Button type="submit">Salvar</Button>
```

## Integração com Select / Checkbox / RadioGroup

Componentes Radix não funcionam com `register()` direto — use `Controller`:

```tsx
import { Controller } from 'react-hook-form'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

<Controller
  control={control}
  name="employment_type"
  render={({ field }) => (
    <Select value={field.value} onValueChange={field.onChange}>
      <SelectTrigger>
        <SelectValue placeholder="Selecione o tipo" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="clt">CLT</SelectItem>
        <SelectItem value="pj">PJ</SelectItem>
      </SelectContent>
    </Select>
  )}
/>
```

## Arrays e sub-objetos

Use `useFieldArray`. Para nested objects, o dot-path funciona:

```tsx
<Input {...register('address.city')} />
<Input {...register('responsibilities.0')} />
```

Pra arrays dinâmicos (skills, benefits):

```tsx
const { fields, append, remove } = useFieldArray({ control, name: 'skills' })
```

## Acessibilidade

- `id` no input + `htmlFor` no Label (ou wrapper shadcn `<Label>` que já resolve).
- `aria-invalid={!!errors.field}` quando há erro.
- `role="alert"` na mensagem de erro (anunciado por screen reader).
- Erro vinculado via `aria-describedby`:

```tsx
<Input
  id="email"
  aria-invalid={!!errors.email}
  aria-describedby={errors.email ? 'email-error' : undefined}
  {...register('email')}
/>
{errors.email && (
  <p id="email-error" role="alert" className="text-xs text-status-error">
    {errors.email.message}
  </p>
)}
```

O wrapper `Field` pode centralizar isso.

## Defaults e pré-preenchimento

- `defaultValues` no `useForm` — não passe `defaultValue` prop por campo (`register` já resolve).
- Para edit form: `reset(initial)` dentro de `useEffect([initial])`.

```tsx
// ✅ edit
useEffect(() => {
  if (job) reset(job)
}, [job, reset])
```

## Rules

- **Schema Zod primeiro** em `src/lib/schemas/`; tipos via `z.infer`.
- **Mensagens em PT-BR** (ou via `t()` se i18n).
- **`zodResolver`** no `useForm`.
- **Sem `useState` controlado** em forms > 2 campos.
- **`noValidate` no `<form>`** — a validação é Zod.
- **`applyServerErrors` + `extractErrorMessage`** em toda falha de API.
- **`isSubmitting`** desabilita o submit.
- **`reset()` após sucesso**, `onSuccess(data)` para o pai.
- **`Controller`** para Select/Checkbox/RadioGroup shadcn (não `register`).
- **Wrapper `Field`** para label + erro + aria.
- **`aria-invalid` + `role="alert"`** sempre que houver erro.
