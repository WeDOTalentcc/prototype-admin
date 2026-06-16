# Form Patterns Reference - Design System LIA v4.1

## Vertical Form (Default)
```html
<form class="space-y-4">
  <div class="space-y-1">
    <label class="block text-[11px] font-semibold text-gray-800">Nome</label>
    <input type="text" class="w-full px-3 py-2 text-sm border border-gray-200 rounded" />
  </div>
  <div class="space-y-1">
    <label class="block text-[11px] font-semibold text-gray-800">Email</label>
    <input type="email" class="w-full px-3 py-2 text-sm border border-gray-200 rounded" />
  </div>
  <div class="flex justify-end gap-2 pt-2">
    <button type="button" class="px-4 py-2 text-sm border border-gray-300 rounded">Cancelar</button>
    <button type="submit" class="px-4 py-2 text-sm bg-gray-900 text-white rounded">Salvar</button>
  </div>
</form>
```

## 2-Column Form
```html
<form class="space-y-4">
  <div class="grid grid-cols-2 gap-4">
    <div class="space-y-1">
      <label>Nome</label>
      <input type="text" />
    </div>
    <div class="space-y-1">
      <label>Sobrenome</label>
      <input type="text" />
    </div>
  </div>
</form>
```

## Validation - Valid Field
```html
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800">Email</label>
  <div class="relative">
    <input type="email" value="user@example.com"
      class="w-full px-3 py-2 text-sm border border-green-300 rounded bg-green-50 pr-10"
      aria-invalid="false" />
    <svg class="absolute right-3 top-2.5 w-5 h-5 text-green-600"><!-- Check --></svg>
  </div>
</div>
```

## Validation - Error Field
```html
<div class="space-y-1">
  <label class="block text-[11px] font-semibold text-gray-800">Email</label>
  <input type="email"
    class="w-full px-3 py-2 text-sm border border-red-300 rounded bg-red-50"
    aria-invalid="true" aria-describedby="email-error" />
  <p id="email-error" class="text-xs text-red-600 flex items-center gap-1">
    <svg class="w-3 h-3"><!-- X --></svg> Email inválido
  </p>
</div>
```

## Required Field
```html
<label class="block text-[11px] font-semibold text-gray-800">
  Nome <span class="text-red-600">*</span>
</label>
```

## ARIA Attributes
- `aria-required="true"` - Required fields
- `aria-invalid="true/false"` - Validation state
- `aria-describedby="error-id"` - Link to error message
- `for="input-id"` - Link label to input
