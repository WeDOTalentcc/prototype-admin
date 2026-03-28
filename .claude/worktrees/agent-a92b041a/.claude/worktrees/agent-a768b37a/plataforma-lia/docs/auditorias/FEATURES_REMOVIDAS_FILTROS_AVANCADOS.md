# Features Removidas - Filtros Avançados

**Data de Remoção:** 22 de dezembro de 2025
**Objetivo:** Simplificar a interface de filtros avançados removendo features não utilizadas para reimplementação futura.

---

## 1. Opções de Qualidade

### Descrição
Seção dentro de "Opções de Busca" que permitia controlar a qualidade dos resultados da busca.

### Localização no Modal
- Sidebar: "Opções de Busca" (ppiOptions)
- Posição: Após a seção "Custo Estimado"

### Campos Removidos

#### 1.1 Dados Atualizados (`highFreshness`)
```typescript
// Estado no filtro
filters.ppiOptions?.highFreshness: boolean

// Comportamento
- Switch toggle (on/off)
- Label: "Dados Atualizados"
- Descrição: "Perfis em tempo real"
- Ícone: RefreshCw (lucide-react)
- Propósito: Buscar apenas perfis com dados recentemente atualizados
```

**Implementação UI:**
```tsx
<div className="flex items-center justify-between p-2.5 rounded-lg border border-gray-100">
  <div className="flex items-center gap-2">
    <RefreshCw className="w-3.5 h-3.5 text-gray-500" />
    <div>
      <div className="text-xs font-medium">Dados Atualizados</div>
      <div className="text-[11px] text-gray-600">
        Perfis em tempo real
      </div>
    </div>
  </div>
  <Switch
    checked={filters.ppiOptions?.highFreshness || false}
    onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "highFreshness", checked)}
  />
</div>
```

#### 1.2 Filtros Rigorosos (`strictFilters`)
```typescript
// Estado no filtro
filters.ppiOptions?.strictFilters: boolean

// Comportamento
- Switch toggle (on/off)
- Label: "Filtros Rigorosos"
- Descrição: "Matching exato de títulos"
- Ícone: Filter (lucide-react)
- Propósito: Exigir correspondência exata dos títulos de cargo
```

**Implementação UI:**
```tsx
<div className="flex items-center justify-between p-2.5 rounded-lg border border-gray-100">
  <div className="flex items-center gap-2">
    <Filter className="w-3.5 h-3.5 text-gray-500" />
    <div>
      <div className="text-xs font-medium">Filtros Rigorosos</div>
      <div className="text-[11px] text-gray-600">
        Matching exato de títulos
      </div>
    </div>
  </div>
  <Switch
    checked={filters.ppiOptions?.strictFilters || false}
    onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "strictFilters", checked)}
  />
</div>
```

---

## 2. Localização

### Descrição
Seção completa de filtros de localização geográfica para busca de candidatos.

### Localização no Modal
- Sidebar: "Localização" (locations)
- Ícone: MapPin (lucide-react)
- Descrição: "Cidades, países e regiões"

### Componentes Removidos

#### 2.1 LocationFilterInput
**Arquivo:** `plataforma-lia/src/components/search/LocationFilterInput.tsx`

**Funcionalidades:**
- Input com autocomplete para cidades, países e regiões
- Dropdown com categorias (CITIES, COUNTRIES, REGIONS)
- Navegação por setas do teclado
- Remoção individual de localizações
- Botão "Limpar tudo"

**Props:**
```typescript
interface LocationFilterInputProps {
  value: LocationItem[]
  onChange: (locations: LocationItem[]) => void
  radius?: RadiusValue
  onRadiusChange?: (radius: RadiusValue) => void
  timezone?: string | null
  onTimezoneChange?: (timezone: string | null) => void
  placeholder?: string
  showRadius?: boolean
  showTimezone?: boolean
  showPresets?: boolean
}

interface LocationItem {
  value: string
  type: 'city' | 'country' | 'region'
}
```

**Dados Estáticos:**
- 45 cidades principais (EUA, Brasil, Europa, Ásia)
- 21 países
- 23 regiões/estados

#### 2.2 RadiusDropdown
**Arquivo:** `plataforma-lia/src/components/search/RadiusDropdown.tsx`

**Opções de Raio:**
```typescript
type RadiusValue = 
  | 'exact'          // Localização exata
  | '15mi' | '25mi' | '50mi' | '100mi' | '150mi' | '200mi'  // Milhas
  | '15km' | '25km' | '50km' | '100km' | '200km'             // Quilômetros

const RADIUS_OPTIONS = [
  { value: 'exact', label: 'Localização exata', description: 'Encontrar pessoas exatamente na(s) localização(ões) selecionada(s)' },
  { value: '15mi', label: 'Até 25 km' },
  { value: '25mi', label: 'Até 40 km' },
  { value: '50mi', label: 'Até 80 km' },
  { value: '100mi', label: 'Até 160 km' },
  { value: '150mi', label: 'Até 240 km' },
  { value: '200mi', label: 'Até 320 km' },
  { value: '15km', label: 'Até 15 km', isSeparator: true },
  { value: '25km', label: 'Até 25 km' },
  { value: '50km', label: 'Até 50 km' },
  { value: '100km', label: 'Até 100 km' },
  { value: '200km', label: 'Até 200 km' },
]
```

#### 2.3 TimezoneDropdown
**Arquivo:** `plataforma-lia/src/components/search/TimezoneDropdown.tsx`

**Fusos Horários Suportados:**
```typescript
const TIMEZONE_OPTIONS = [
  // North America
  { value: 'EST', label: 'Eastern Standard Time', offset: 'UTC-5:00' },
  { value: 'CST', label: 'Central Standard Time', offset: 'UTC-6:00' },
  { value: 'MST', label: 'Mountain Standard Time', offset: 'UTC-7:00' },
  { value: 'PST', label: 'Pacific Standard Time', offset: 'UTC-8:00' },
  { value: 'AKST', label: 'Alaska Standard Time', offset: 'UTC-9:00' },
  { value: 'HST', label: 'Hawaii Standard Time', offset: 'UTC-10:00' },
  { value: 'AST', label: 'Atlantic Standard Time', offset: 'UTC-4:00' },
  { value: 'NST', label: 'Newfoundland Standard Time', offset: 'UTC-3:30' },
  
  // South America
  { value: 'BRT', label: 'Brasília Time', offset: 'UTC-3:00' },
  { value: 'ART', label: 'Argentina Time', offset: 'UTC-3:00' },
  { value: 'CLT', label: 'Chile Standard Time', offset: 'UTC-4:00' },
  
  // Europe
  { value: 'GMT', label: 'GMT/UTC', offset: 'UTC+0:00' },
  { value: 'CET', label: 'Central European Time', offset: 'UTC+1:00' },
  { value: 'EET', label: 'Eastern European Time', offset: 'UTC+2:00' },
  
  // Asia/Pacific
  { value: 'IST', label: 'India Standard Time', offset: 'UTC+5:30' },
  { value: 'CST_CN', label: 'China Standard Time', offset: 'UTC+8:00' },
  { value: 'JST', label: 'Japan Standard Time', offset: 'UTC+9:00' },
  { value: 'AEST', label: 'Australian Eastern Time', offset: 'UTC+10:00' },
]
```

#### 2.4 PastLocationsInput
**Arquivo:** `plataforma-lia/src/components/search/PastLocationsInput.tsx`

**Funcionalidades:**
- Buscar candidatos por histórico de localizações anteriores
- Mesmo autocomplete do LocationFilterInput
- Placeholder: "Ex: São Paulo / Brasil / RJ / ..."
- Label: "Past Locations"

**Props:**
```typescript
interface PastLocationsInputProps {
  value: PastLocationItem[]
  onChange: (locations: PastLocationItem[]) => void
  placeholder?: string
}
```

#### 2.5 LocationPresetsModal
**Arquivo:** `plataforma-lia/src/components/search/LocationPresetsModal.tsx`

**Presets Globais Pré-definidos:**
1. **US Major Cities** - 24 cidades principais dos EUA
2. **US Tech Hubs** - 14 hubs tecnológicos dos EUA
3. **Brazil Major Cities** - 18 cidades principais do Brasil
4. **Latin America Capitals** - 12 capitais latino-americanas
5. **Europe Major Cities** - 19 cidades europeias principais
6. **APAC Tech Hubs** - 12 hubs tecnológicos da Ásia-Pacífico
7. **Remote Friendly Timezones** - EUA, Canadá, México
8. **English Speaking Countries** - 6 países anglófonos
9. **DACH Region** - Alemanha, Áustria, Suíça
10. **Nordic Countries** - 5 países nórdicos

**Funcionalidades:**
- Tabs: Organization Presets / General Presets
- Busca por nome ou descrição
- Visualização de localizações incluídas
- Criação de presets personalizados (Organization)

### Estado do Filtro
```typescript
// Em SearchFilters
locations?: {
  locationItems?: LocationItem[]
  locations?: string[]      // Cidades (derivado de locationItems)
  countries?: string[]      // Países (derivado de locationItems)
  radius?: RadiusValue
  timezone?: string | null
  pastLocations?: PastLocationItem[]
}
```

### Integração na Sidebar
```typescript
// Em sidebarCategories
{ key: "locations", label: "Localização", icon: MapPin }

// Em categories (com descrição)
{ key: "locations", label: "Localização", icon: MapPin, description: "Cidades e países" }
```

---

## 3. Arquivos de Componentes Preservados

Os seguintes arquivos NÃO foram deletados e podem ser reutilizados:

1. `plataforma-lia/src/components/search/LocationFilterInput.tsx`
2. `plataforma-lia/src/components/search/RadiusDropdown.tsx`
3. `plataforma-lia/src/components/search/TimezoneDropdown.tsx`
4. `plataforma-lia/src/components/search/PastLocationsInput.tsx`
5. `plataforma-lia/src/components/search/LocationPresetsModal.tsx`

---

## 4. Parâmetros de API (Backend)

### Pearch API Parameters (Referência)
```typescript
// Opções de Qualidade
high_freshness?: boolean  // Dados Atualizados
strict_filters?: boolean  // Filtros Rigorosos

// Localização
locations?: string[]      // Array de localizações (cidades)
countries?: string[]      // Array de países
location_radius?: string  // Raio de busca (ex: "25mi", "50km")
timezone?: string         // Fuso horário preferido
past_locations?: string[] // Histórico de localizações
```

---

## 5. Notas de Reimplementação

### Considerações para Reimplementação:

1. **Opções de Qualidade:**
   - Verificar se Pearch API ainda suporta `high_freshness` e `strict_filters`
   - Considerar impacto no custo de créditos
   - Avaliar UX/feedback visual quando ativado

2. **Localização:**
   - Considerar integração com API de geocoding (Google Places, Mapbox)
   - Implementar busca semântica para localizações
   - Adicionar mapa visual para seleção de áreas
   - Considerar clusters geográficos pré-definidos por indústria

3. **Performance:**
   - Autocomplete com debounce (400ms recomendado)
   - Cache de resultados de busca de localização
   - Lazy loading de presets

---

## 6. Screenshots de Referência

Ver arquivos anexados:
- `attached_assets/Screen_Shot_2025-12-22_at_3.20.51_PM_1766427653968.png` - Opções de Qualidade
- `attached_assets/Screen_Shot_2025-12-22_at_3.21.59_PM_1766427721296.png` - Seção Localização

---

*Documento criado para referência futura. Manter atualizado conforme necessário.*
