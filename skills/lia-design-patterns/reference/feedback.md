# Feedback Patterns Reference - Design System LIA v4.1

## Alert Messages

### Success
```html
<div class="flex items-start gap-3 bg-green-50 border border-green-200 rounded-md p-4">
  <svg class="w-5 h-5 text-green-600 flex-shrink-0"><!-- Check --></svg>
  <div class="flex-1">
    <h4 class="text-sm font-semibold text-green-900">Sucesso!</h4>
    <p class="text-sm text-green-700 mt-0.5">Dados salvos com sucesso.</p>
  </div>
</div>
```

### Error
```html
<div class="flex items-start gap-3 bg-red-50 border border-red-200 rounded-md p-4">
  <svg class="w-5 h-5 text-red-600 flex-shrink-0"><!-- X --></svg>
  <div class="flex-1">
    <h4 class="text-sm font-semibold text-red-900">Erro</h4>
    <p class="text-sm text-red-700 mt-0.5">Não foi possível salvar.</p>
  </div>
</div>
```

### Warning
```html
<div class="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-md p-4">
  <svg class="w-5 h-5 text-amber-600 flex-shrink-0"><!-- Alert --></svg>
  <div class="flex-1">
    <h4 class="text-sm font-semibold text-amber-900">Atenção</h4>
    <p class="text-sm text-amber-700 mt-0.5">Esta ação não pode ser desfeita.</p>
  </div>
</div>
```

## Empty States
```html
<div class="py-16 text-center">
  <svg class="w-16 h-16 text-gray-400 mx-auto mb-4"><!-- Empty icon --></svg>
  <h3 class="text-base font-semibold text-gray-900 mb-1">Nenhum candidato encontrado</h3>
  <p class="text-sm text-gray-600 mb-4">Comece adicionando candidatos à sua vaga</p>
  <button class="px-4 py-2 bg-gray-900 text-white text-sm font-semibold rounded">
    Adicionar Candidato
  </button>
</div>
```

## Error Pages

### 404
```html
<div class="min-h-screen flex items-center justify-center p-6">
  <div class="text-center max-w-md">
    <h1 class="text-6xl font-bold text-gray-900 mb-2">404</h1>
    <h2 class="text-2xl font-semibold text-gray-900 mb-2">Página não encontrada</h2>
    <p class="text-sm text-gray-600 mb-6">A página que você está procurando não existe ou foi movida.</p>
    <a href="/" class="inline-block px-6 py-3 bg-gray-900 text-white rounded font-semibold">Voltar ao início</a>
  </div>
</div>
```

### 500
```html
<div class="min-h-screen flex items-center justify-center p-6">
  <div class="text-center max-w-md">
    <h1 class="text-6xl font-bold text-gray-900 mb-2">500</h1>
    <h2 class="text-2xl font-semibold text-gray-900 mb-2">Erro no servidor</h2>
    <p class="text-sm text-gray-600 mb-6">Algo deu errado. Nossa equipe já foi notificada.</p>
    <button class="px-6 py-3 bg-gray-900 text-white rounded font-semibold">Tentar novamente</button>
  </div>
</div>
```
