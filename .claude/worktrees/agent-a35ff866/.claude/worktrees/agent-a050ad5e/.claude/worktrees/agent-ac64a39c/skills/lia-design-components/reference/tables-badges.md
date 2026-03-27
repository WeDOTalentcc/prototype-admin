# Tables & Badges Reference - Design System LIA v4.1

## Tables

### Basic Structure
```html
<div class="bg-white rounded-md border border-gray-200 overflow-hidden">
  <table class="w-full">
    <thead class="bg-gray-50 border-b border-gray-200">
      <tr>
        <th class="px-6 py-3 text-left text-[11px] font-semibold text-gray-800 font-['Inter']">NOME</th>
        <th class="px-6 py-3 text-left text-[11px] font-semibold text-gray-800">STATUS</th>
        <th class="px-6 py-3 text-left text-[11px] font-semibold text-gray-800">SCORE</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-200">
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4 text-sm text-gray-900 font-['Inter']">João Silva</td>
        <td class="px-6 py-4">
          <span class="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium bg-green-50 text-green-700 border border-green-200">Ativo</span>
        </td>
        <td class="px-6 py-4 text-sm text-gray-900 font-['Inter']" style="font-feature-settings: 'tnum' 1;">95</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- Vuetify -->
<v-data-table :headers="headers" :items="items" class="elevation-1">
  <template #item.status="{ item }">
    <v-chip color="green" size="small" variant="outlined">{{ item.status }}</v-chip>
  </template>
</v-data-table>
```

### Row Actions
```html
<td class="px-6 py-4">
  <div class="flex items-center gap-1">
    <button class="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded" aria-label="Editar">
      <svg class="w-4 h-4">...</svg>
    </button>
    <button class="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded" aria-label="Deletar">
      <svg class="w-4 h-4">...</svg>
    </button>
  </div>
</td>
```

### Empty State
```html
<div class="py-12 text-center">
  <svg class="w-12 h-12 text-gray-400 mx-auto mb-3">...</svg>
  <h3 class="text-sm font-semibold text-gray-900 mb-1">Nenhum registro encontrado</h3>
  <p class="text-xs text-gray-600">Tente ajustar os filtros</p>
</div>
```

---

## Badges & Tags

### Standard (Gray)
```html
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-gray-100 text-gray-700 border border-gray-200 font-['Inter']">Badge</span>
<v-chip size="small" variant="outlined">Badge</v-chip>
```

### Semantic Badges
```html
<!-- Success -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-green-50 text-green-700 border border-green-200">Ativo</span>
<!-- Warning -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">Pendente</span>
<!-- Error -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-red-50 text-red-700 border border-red-200">Rejeitado</span>

<!-- Vuetify -->
<v-chip color="green" size="small" variant="outlined">Ativo</v-chip>
<v-chip color="amber" size="small" variant="outlined">Pendente</v-chip>
<v-chip color="red" size="small" variant="outlined">Rejeitado</v-chip>
```

### WeDo Accent Badges (10%)
```html
<!-- Cyan (LIA) -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#60BED1] border border-[#60BED1]/20" style="background: rgba(96,190,209,0.1);">LIA</span>
<!-- Green (Candidatos) -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#5DA47A] border border-[#5DA47A]/20" style="background: rgba(93,164,122,0.1);">Candidato</span>
<!-- Orange (Tempo) -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#D19960] border border-[#D19960]/20" style="background: rgba(209,153,96,0.1);">Urgente</span>
<!-- Purple (Insights) -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#9860D1] border border-[#9860D1]/20" style="background: rgba(152,96,209,0.1);">Insight</span>
```

### Badge with Icon
```html
<span class="inline-flex items-center gap-1 px-2 py-1 rounded-sm text-[10px] font-medium bg-green-50 text-green-700 border border-green-200">
  <svg class="w-3 h-3">...</svg>
  <span>Aprovado</span>
</span>
```
